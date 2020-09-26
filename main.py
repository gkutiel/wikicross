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


if __name__ == '__main__':
    # xml_2_json()
    data_json_2_defs_json()
