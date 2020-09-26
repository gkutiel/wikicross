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


def data_json_2_defs_json():
    with open('data.json') as f:
        with open('defs.json', 'w', encoding='utf-8') as o:
            for l in f:
                row = json.loads(l)
                title, text = row['title'], row['text']
                if ':' in title:
                    continue
                def_text = d(text)
                if def_text and not title in def_text:
                    print(json.dumps({'title': title, 'def': def_text}, ensure_ascii=False), file=o)


def gen():
    n = 8
    grid = [['-'] * n for _ in range(n)]

    def can_fit_h(w: str, i: int, j: int):
        for d in range(len(w)):
            if grid[i][j+d] not in ['-', w[d]]:
                return False

        return True

    def can_fit_v(w: str, i: int, j: int):
        for d in range(len(w)):
            if grid[i+d][j] not in ['-', w[d]]:
                return False

        return True

    def mark(i, j):
        if 0 <= i < n and 0 <= j < n:
            grid[i][j] = grid[i][j] or '*'

    trans = ''.maketrans(
        'ךםןףץ',
        'כמנפצ',
        ' \'"״',
    )

    h_defs = []

    def fit_h(d):
        w = d['title'].translate(trans)
        m = len(w)
        for i in range(n):
            for j in range(n - m + 1):
                if can_fit_h(w, i, j):
                    h_defs.append((i, j))
                    grid[i][j:j+m] = list(w)
                    mark(i, j-1)
                    mark(i, j+m)
                    return True

    v_defs = []

    def fit_v(d):
        w = d['title'].translate(trans)
        m = len(w)
        for i in range(n - m + 1):
            for j in range(n):
                if can_fit_v(w, i, j):
                    v_defs.append((i, j))
                    for k, c in enumerate(w):
                        grid[i+k][j] = c

                    mark(i-1, j)
                    mark(i+m, j)
                    return True

    def len_title(d):
        return len(d['title'])

    defs = random.sample([json.loads(l) for l in open('defs.json')], 1000)
    defs = [d for d in defs if len_title(d) <= n]
    print(len(defs))
    defs.sort(key=len_title, reverse=True)
    h = False
    for d in defs:
        if h:
            h = not fit_h(d)
        else:
            h = fit_v(d)

    print(len(h_defs), len(v_defs), len(set(v_defs + h_defs)))
    print(*grid, sep='\n')


if __name__ == '__main__':
    # xml_2_json()
    # data_json_2_defs_json()
    gen()
