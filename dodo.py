from doit.tools import run_once
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

    def has_en(text):
        return re.search('[a-z]', text, flags=re.IGNORECASE)

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


def gen(n=20, sample=3000):
    grid = [[None] * n for _ in range(n)]

    def can_fit_h(w: str, i: int, j: int):
        for d in range(len(w)):
            if grid[i][j+d] not in [None, w[d]]:
                return False

        return True

    def can_fit_v(w: str, i: int, j: int):
        for d in range(len(w)):
            if grid[i+d][j] not in [None, w[d]]:
                return False

        return True

    h_defs = {}

    def lens(d):
        return ','.join(reversed([str(len(w)) for w in d["title"].split()]))

    def fit_h(d):
        w = d['word']
        m = len(w)
        for i in range(n):
            for j in range(n - m + 1):
                if can_fit_h(w, i, j):
                    h_defs[(i, j)] = f'{d["def"]} ({lens(d)})'
                    grid[i][j:j+m] = list(w)
                    return True

    v_defs = {}

    def fit_v(d):
        w = d['word']
        m = len(w)
        for i in range(n - m + 1):
            for j in range(n):
                if can_fit_v(w, i, j):
                    v_defs[(i, j)] = f'{d["def"]} ({lens(d)})'
                    for k, c in enumerate(w):
                        grid[i+k][j] = c

                    return True

    def len_word(d):
        return len(d['word'])

    defs = random.sample(
        [json.loads(l) for l in open('defs.json')],
        sample
    )
    defs = [d for d in defs if 2 <= len_word(d) <= n]
    defs.sort(key=len_word, reverse=True)

    h = False
    for d in defs:
        if h:
            h = not fit_h(d)
        else:
            h = fit_v(d)

    return grid, h_defs, v_defs


def to_latex(grid, hdefs, vdefs, title='', out=Path('.') / 'main.tex'):
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
            \begin{document}
            \maketitle
            \begin{center}
            \begin{tikzpicture}[x=-1cm,y=-1cm]
        ''', file=f)

        for i in range(n):
            for j in range(n):
                if grid[i][j] in [None, '*']:
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
                if grid[i][j] in [None, '*']:
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
    for n in [6, 10, 15, 20]:
        for j in range(9):
            out_dir = docs / f'{n}X{n}'

            yield {
                'name': f'mkdir:{n}:{j}',
                'actions': [f'mkdir -p {out_dir}'],
            }

            tex = out_dir / f'{j:0>4}.tex'

            yield {
                'name': f'latex:{n}:{j}',
                'actions': [lambda: to_latex(*gen(n=n), out=tex)],
                'targets': [tex],
                'uptodate': [run_once],
            }

            pdf = tex.with_suffix('.pdf')

            yield {
                'name': f'latex:{n}:{j}',
                'actions': [f'latexmk -xelatex -outdir={out_dir} {tex}'],
                'file_dep': [tex],
                'targets': [pdf]
            }
