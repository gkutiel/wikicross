from typing import Tuple
from doit.tools import run_once
import numpy as np
from numpy import ndarray as nd
from pathlib import Path
import random
import json
import re
from os import name
from xml.dom.minidom import parse


def task_download_xml():
    dump = 'https://dumps.wikimedia.org/hewiktionary/latest/hewiktionary-latest-pages-meta-current.xml.bz2'
    return {
        'actions': [f'wget {dump}'],
        'targets': ['hewiktionary-latest-pages-meta-current.xml.bz2'],
        'uptodate': [run_once],
    }


def task_dtrx():
    return {
        'actions': [
            'dtrx hewiktionary-latest-pages-meta-current.xml.bz2',
            'mv hewiktionary-latest-pages-meta-current.xml data.xml'
        ],
        'file_dep': ['hewiktionary-latest-pages-meta-current.xml.bz2'],
        'targets': ['data.xml'],
    }


def task_xml_2_json():
    def t(node):
        return ''.join([n.data for n in node.childNodes if n.nodeType == n.TEXT_NODE])

    def xml_2_json():
        with open('data.xml') as f:
            dom = parse(f)

        with open('data.json', 'w', encoding='utf-8') as o:
            for page in dom.getElementsByTagName('page'):
                title = page.getElementsByTagName('title')
                text = page.getElementsByTagName('text')
                if title and text:
                    print(
                        json.dumps({
                            'title': t(title[0]),
                            'text': t(text[0])
                        }, ensure_ascii=False),
                        file=o
                    )

    return {
        'actions': [xml_2_json],
        'file_dep': ['data.xml'],
        'targets': ['data.json'],
        'verbosity': 2,
    }


def has_en(text):
    return re.search('[a-z]', text, flags=re.IGNORECASE)


def task_data_2_defs():
    def d(text):
        p1 = re.compile(r'\{\{[^{}]*\}\}')
        p2 = re.compile(r'[^\[\]]+\|([^\[\]]+)')
        p3 = re.compile(r'\[\[|\]\]')
        for l in text.split('\n'):
            if l and l[0] == '#':
                return re.sub(
                    p3,
                    '',
                    re.sub(
                        p2,
                        r'\g<1>',
                        re.sub(
                            p1,
                            '',
                            l[1:]
                        )
                    )
                ).replace('{', r'\{').replace('}', r'\}').strip()

        return ''

    def data_json_2_defs_json():
        trans = ''.maketrans(
            'ךםןףץ',
            'כמנפצ',
            ' #\'"״',
        )

        with open('data.json') as f:
            with open('defs.json', 'w', encoding='utf-8') as o:
                for l in f:
                    row = json.loads(l)
                    title, text = row['title'], row['text']
                    if (
                        ':' in title
                        or '"' in title
                        or "'" in title
                        or has_en(title)
                    ):
                        continue

                    def_text = d(text)
                    if (
                        def_text
                        and not title in def_text
                        and not 'הפניה' in def_text
                        and not has_en(def_text)
                    ):
                        print(
                            json.dumps({
                                'title': title,
                                'word': title.translate(trans),
                                'def': def_text,
                            },
                                ensure_ascii=False),
                            file=o
                        )

    return {
        'actions': [data_json_2_defs_json],
        'file_dep': ['data.json'],
        'targets': ['defs.json'],
    }


empty, blocked = '.', ','


def free(grid, cell: nd):
    n = len(grid)
    i, j = cell
    if 0 <= i < n and 0 <= j < n:
        return grid[i][j] in [empty, blocked]

    return True


def fit(grid, start: nd, d: nd, word: str):
    assert d.shape == (2,)
    m = len(word)
    end = start + d * m
    di, dj = d
    assert di * dj == 0
    assert di + dj == 1

    if not free(grid, start - d) or not free(grid, end):
        return False

    (i1, j1), (i2, j2) = start, end
    ref = grid[i1, j1:j2] if dj else grid[i1:i2, j1]
    for i, c in enumerate(ref):
        if c not in [empty, word[i]]:
            return False

    return True


def gen(seed, n=7):
    random.seed(seed)
    grid = np.full((n, n), empty)
    for i in range(1, n, 2):
        for j in range(1, n, 2):
            grid[i][j] = blocked

    def block(i, j):
        if 0 <= i < n and 0 <= j < n:
            grid[i][j] = blocked

    h_defs = {}
    v_defs = {}

    def lens(de):
        return ','.join(reversed([str(len(w)) for w in de["title"].split()]))

    def place(de, d: nd):
        w = de['word']
        m = len(w)
        di, dj = d
        assert di * dj == 0
        assert di + dj == 1
        for i in range(n - (m - 1) * di):
            for j in range(n - (m - 1) * dj):
                start = np.array([i, j])
                end = start + m * d
                if fit(grid, start, d, w):
                    # print(w)
                    # print(grid)
                    s = f'{de["def"]} ({lens(de)})'
                    if di:
                        v_defs[(i, j)] = s
                        grid[i:i+m, j] = list(w)
                    else:
                        h_defs[(i, j)] = s
                        grid[i, j:j+m] = list(w)

                    block(i-di, j-dj)
                    block(i+di*m, j+dj*m)
                    # print(grid)
                    return np.array([dj, di])
        return d

    defs = [[] for i in range(n + 1)]
    words = {}
    for d in [json.loads(l) for l in open('defs.json')]:
        word = d['word']
        l = len(word)
        if l > n:
            continue

        defs[l].append(d)
        words[word] = d

    for l in defs:
        random.shuffle(l)

    d = np.array([1, 0])
    for length in range(n, 1, -1):
        for de in defs[length]:
            d = place(de, d)

    trans = ''.maketrans('', '', empty + blocked)
    for i in range(n):
        for j in range(n):
            cells = np.array([
                [i, j],
                [i-2, j],
                [i+2, j],
                [i, j-2],
                [i, j+2],
            ])
            if (
                not free(grid, cells[0])
                or not free(grid, cells[1])
                or not free(grid, cells[2])
                or not free(grid, cells[3])
                or not free(grid, cells[4])
            ):
                continue

            for c in 'אבגדהוזחטיכלמנסעפצקרשת' + blocked:
                grid[i][j] = c
                if c == blocked:
                    break

                h_word = ''.join(grid[i, j-1:j+2]).translate(trans)
                v_word = ''.join(grid[i-1:i+2, j]).translate(trans)
                if h_word != v_word and h_word in words and v_word in words:
                    h_cord = (i, j) if grid[i][j-1] in [empty, blocked] else (i, j-1)
                    hd = words[h_word]
                    h_defs[h_cord] = f'{hd["def"]} ({lens(hd)})'

                    v_cord = (i, j) if grid[i-1][j] in [empty, blocked] else (i-1, j)
                    vd = words[v_word]
                    v_defs[v_cord] = f'{vd["def"]} ({lens(vd)})'
                    del words[h_word]
                    del words[v_word]
                    break

    return grid, h_defs, v_defs


def to_latex(grid, hdefs, vdefs, out, title=''):
    n = len(grid)
    corrs = set(list(hdefs.keys()) + list(vdefs.keys()))
    corrs = {cor: i+1 for i, cor in enumerate(sorted(corrs))}

    with open(out, 'w') as f:
        print(r'''
            \nonstopmode
            \documentclass{article}
            \usepackage{tikz}
            \usepackage{polyglossia}
            \usepackage[margin=0.8cm]{geometry}
            \newfontfamily\hebrewfont[Script=Hebrew]{Hadasim CLM}
            \setdefaultlanguage[numerals=hebrew]{hebrew}
            \setotherlanguage{english}
        ''', file=f)

        print(f'\\title{{{title}}}', file=f)

        print(r'''
            \author{גלעד קותיאל}
            \date{}
            \begin{document}
            \maketitle
            \begin{center}
            \begin{tikzpicture}[x=-1cm,y=-1cm]
        ''', file=f)

        for i in range(n):
            for j in range(n):
                if grid[i][j] in [empty, blocked]:
                    print(f'\\fill ({j},{i}) rectangle +(1,1);', file=f)

        for (i, j), k in corrs.items():
            print(f'\\node[below left] at({j}, {i}) {{\\small {k}}};', file=f)

        print(f'''\\foreach \\x in {{0,...,{n}}}{{
                \\draw[thick] (\\x,0) -- (\\x,{n});
                \\draw[thick] (0,\\x) -- ({n},\\x);
                }}
        ''', file=f)

        print(r'''\end{tikzpicture}
                \end{center}
        ''', file=f)

        print(r'\subsection*{מאוזן}', file=f)
        print(r'\begin{enumerate}', file=f)
        for cor, d in sorted(hdefs.items(), key=lambda x: corrs[x[0]]):
            print(f'\\item[{corrs[cor]}.] {d}', file=f)
        print(r'\end{enumerate}', file=f)

        print(r'\subsection*{מאונך}', file=f)
        print(r'\begin{enumerate}', file=f)
        for cor, d in sorted(vdefs.items(), key=lambda x: corrs[x[0]]):
            print(f'\\item[{corrs[cor]}.] {d}', file=f)
        print(r'\end{enumerate}', file=f)

        print(r'''\pagebreak
                \begin{center}
                \begin{tikzpicture}[x=-1cm,y=-1cm]
        ''', file=f)

        for i in range(n):
            for j in range(n):
                if grid[i][j] in [empty, blocked]:
                    print(f'\\fill ({j},{i}) rectangle +(1,1);', file=f)
                else:
                    print(f'\\node[] at({j + .5}, {i + .5}) {{{grid[i][j]}}};', file=f)

        for (i, j), k in corrs.items():
            print(f'\\node[below left] at({j}, {i}) {{\\small {k}}};', file=f)

        print(f'''\\foreach \\x in {{0,...,{n}}}{{
                \\draw[thick] (\\x,0) -- (\\x,{n});
                \\draw[thick] (0,\\x) -- ({n},\\x);
                }}
        ''', file=f)

        print(r'''\end{tikzpicture}
                \end{center}
        ''', file=f)

        print(r'\end{document}', file=f)


def task_gen():
    docs = Path('docs')

    def out_dir(n):
        return docs / f'{n}X{n}'

    def git_keep(n):
        return out_dir(n) / '.gitkeep'

    def tex(n, i):
        return out_dir(n) / f'{i:0>4}.tex'

    def pdf(n, i):
        return tex(n, i).with_suffix('.pdf')

    def gen_tex(n, i):
        return lambda: to_latex(
            *gen(i, n=n),
            out=tex(n, i),
            title=f'תשבץ {n}X{n} מספר {i + 1}'
        )

    ns = [7, 9, 11, 13]
    # ns = [9]
    r = 6

    def index_html():
        from shooki import (html, head, body, link, div, a, title, h1, h2, p, meta)

        with open(docs / 'index.html', 'w') as f:
            content = div.content[div.title[h1['ויקי-תשבץ']]]
            for n in ns:
                grid = div.grid
                content.append(div.title[h2[f'תשבצים {n}X{n}']])
                content.append(grid)
                for i in range(r):
                    grid.append(div.cell[a(href=f'{n}X{n}/{i:0>4}.pdf')[f'תשבץ מספר {i + 1}']])
            print(
                '<!DOCTYPE html>',
                html(lang='he', dir='auto')[
                    head[
                        title['ויקי-תשבץ'],
                        link(rel='stylesheet', href='index.css'),
                        link(rel='icon', href='favicon.png'),
                        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                        meta(property="og:title", content="ויקי תשבץ"),
                        meta(property="og:description", content="תשבצים מגונרצים מויקימילון"),
                        meta(property="og:image", content="https://gkutiel.github.io/wikicross/favicon.png"),
                    ],
                    body[content],
                ], file=f
            )

    yield {
        'name': 'html',
        'actions': [index_html],
        'targets': [docs / 'index.html'],
    }

    for n in ns:
        yield {
            'name': f'mkdir:{n}',
            'actions': [
                f'mkdir -p {out_dir(n)}',
                f'touch {git_keep(n)}'
            ],
            'targets': [git_keep(n)],
        }

        for i in range(r):
            yield {
                'name': f'tex:{n}:{i}',
                'actions': [gen_tex(n, i)],
                'file_dep': [git_keep(n)],
                'targets': [tex(n, i)],
                'uptodate': [run_once],
                'verbosity': 2,
            }

            yield {
                'name': f'pdf:{n}:{i}',
                'actions': [f'latexmk -xelatex -outdir={out_dir(n)} {tex(n, i)}'],
                'file_dep': [git_keep(n), tex(n, i)],
                'targets': [pdf(n, i)],
                'verbosity': 0,
            }
