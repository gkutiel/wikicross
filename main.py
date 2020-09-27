import random
import json
import re
from os import name
from xml.dom.minidom import parse


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
            ).strip()

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


def gen(n=8, sample=2000):
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

    def fit_h(d):
        w = d['word']
        m = len(w)
        for i in range(n):
            for j in range(n - m + 1):
                if can_fit_h(w, i, j):
                    lens = ','.join([str(len(w)) for w in d["title"].split()])
                    h_defs[(i, j)] = f'{d["def"]} ({lens})'
                    grid[i][j:j+m] = list(w)
                    return True

    v_defs = {}

    def fit_v(d):
        w = d['word']
        m = len(w)
        for i in range(n - m + 1):
            for j in range(n):
                if can_fit_v(w, i, j):
                    lens = ','.join([str(len(w)) for w in d["title"].split()])
                    v_defs[(i, j)] = f'{d["def"]} ({lens})'
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
    defs.sort(
        key=lambda d: random.randint(0, len_word(d)),
        reverse=True
    )
    h = False
    for d in defs:
        if h:
            h = not fit_h(d)
            if not h:
                print(*grid, sep='\n')
                print()
        else:
            h = fit_v(d)
            if h:
                print(*grid, sep='\n')
                print()

    return grid, h_defs, v_defs


def to_latex(grid, hdefs, vdefs):
    n = len(grid)
    corrs = set(list(hdefs.keys()) + list(vdefs.keys()))
    corrs = {cor: i+1 for i, cor in enumerate(corrs)}

    with open('main.tex', 'w') as f:
        print(r'''\documentclass{article}
            \usepackage{tikz}
            \usepackage{polyglossia}
            \usepackage[margin=0.8cm]{geometry}
            \newfontfamily\hebrewfont[Script=Hebrew]{Hadasim CLM}
            \setdefaultlanguage[numerals=hebrew]{hebrew}
            \setotherlanguage{english}

            \begin{document}
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


if __name__ == '__main__':
    # xml_2_json()
    # data_json_2_defs_json()
    # gen()
    to_latex(*gen())
