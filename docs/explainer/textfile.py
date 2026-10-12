"""Read and write docs/explainer/text.md, the explainer's words (headings, page text, tour captions).

Format: one section per page, in tour order.

    ## <id>                  page id: a block (intro, air, lna_chain, ...) or a level (link, chip, chip:tx, chip:rx)
    name: <heading>
    short: <breadcrumb name>  (optional; defaults to the heading)
    sub: <subtitle>
    cap: <tour caption>

    <page text: blank lines separate paragraphs>

Lines before the first section are comments (kept as they are when the edit server writes the file).
In page text, [[block|words]] links the words to that block's page, and {name} is a number from the
simulations (see FILL in template.html).
"""
import os
import re

FIELDS = ['name', 'short', 'sub', 'cap']
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'text.md')


def parse(src):
    """text.md source -> (header lines, {id: {field: value, 'body': text}}) in file order."""
    head, pages, cur, body = [], {}, None, []
    def close():
        if cur is not None:
            paras = re.split(r'\n\s*\n', '\n'.join(body).strip())
            pages[cur]['body'] = '\n\n'.join(' '.join(p.split('\n')).strip() for p in paras if p.strip())
    for line in src.split('\n'):
        m = re.match(r'^## (\S+)\s*$', line)
        if m:
            close()
            cur, body = m.group(1), []
            pages[cur] = {}
            continue
        if cur is None:
            head.append(line)
            continue
        f = re.match(r'^(%s): ?(.*)$' % '|'.join(FIELDS), line)
        if f and not body:
            pages[cur][f.group(1)] = f.group(2).strip()
        else:
            body.append(line)
    close()
    return head, pages


def render(head, pages):
    out = '\n'.join(head).rstrip('\n') + '\n\n' if ''.join(head).strip() else ''
    for pid, p in pages.items():
        out += f'## {pid}\n'
        for f in FIELDS:
            v = ' '.join(str(p.get(f) or '').split())
            if v:
                out += f'{f}: {v}\n'
        body = str(p.get('body') or '').strip()
        if body:
            paras = [' '.join(x.split()) for x in re.split(r'\n\s*\n', body.replace('\r', '')) if x.strip()]
            out += '\n' + '\n\n'.join(paras) + '\n'
        out += '\n'
    return out.rstrip('\n') + '\n'


def load(path=PATH):
    return parse(open(path).read())


def save(pages, path=PATH):
    """Write pages back, keeping the file's header and section order (new ids go at the end)."""
    head, old = load(path) if os.path.exists(path) else ([], {})
    order = [k for k in old if k in pages] + [k for k in pages if k not in old]
    clean = {k: {f: pages[k].get(f, '') for f in FIELDS + ['body']} for k in order}
    tmp = path + '.tmp'
    open(tmp, 'w').write(render(head, clean))
    os.replace(tmp, path)
