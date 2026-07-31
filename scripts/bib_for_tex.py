#!/usr/bin/env python3
"""Build a self-contained .bib holding exactly the references a LaTeX document cites.

Point it at the top-level .tex; \\input and \\include are followed recursively, so
a manuscript split across files needs only its main file named:

    ./bib_for_tex.py ~/manuscripts/paper/main.tex

Writes <stem>_refs.bib beside the source unless -o says otherwise, and resolves
the master library automatically when the script sits in the library's repo.

Only standard bibliographic fields are carried across. Reference-manager private
fields (BibDesk bookmark blobs), RIS import residue, and `month` are dropped --
see KEEP below.
"""
import argparse
import os
import re
import sys

# Standard BibTeX/BibLaTeX fields. `month` is deliberately absent: it is never
# wanted in the reference list, and dropping the field is style-independent --
# a journal .bst that formats months cannot resurrect it.
KEEP = {
    'author', 'editor', 'title', 'booktitle', 'journal', 'year',
    'volume', 'number', 'pages', 'eid', 'publisher', 'institution', 'school',
    'organization', 'series', 'edition', 'chapter', 'address', 'howpublished',
    'doi', 'url', 'isbn', 'issn', 'note', 'type', 'crossref',
}

CITE_RE = re.compile(r'\\[a-zA-Z]*cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}')
# (?![a-zA-Z]) keeps \includegraphics from being mistaken for \include.
INPUT_RE = re.compile(r'\\(?:input|include)(?![a-zA-Z])\s*\{([^}]+)\}')
ENTRY_RE = re.compile(r'@(\w+)\s*\{\s*([^,\s]+)\s*,')
COMMENT_RE = re.compile(r'(?<!\\)%.*')


def read_tex(path, seen):
    """Return the concatenated text of a .tex file and everything it pulls in."""
    path = os.path.abspath(path)
    if path in seen:
        return ''
    seen.add(path)
    try:
        text = open(path, encoding='utf-8', errors='replace').read()
    except FileNotFoundError:
        print(f'warning: cannot read {path}', file=sys.stderr)
        return ''
    # Strip comments so citations inside commented-out text are not collected.
    text = COMMENT_RE.sub('', text)
    out = [text]
    for target in INPUT_RE.findall(text):
        target = target.strip()
        if not os.path.splitext(target)[1]:
            target += '.tex'
        out.append(read_tex(os.path.join(os.path.dirname(path), target), seen))
    return '\n'.join(out)


def cited_keys(tex_path):
    text = read_tex(tex_path, set())
    keys = []
    for group in CITE_RE.findall(text):
        for key in group.split(','):
            key = key.strip()
            if key and key not in keys:
                keys.append(key)
    return keys


def split_entries(bib_text):
    starts = [(m.start(), m.group(1), m.group(2))
              for m in ENTRY_RE.finditer(bib_text)]
    for i, (pos, typ, key) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(bib_text)
        yield key, typ, bib_text[pos:end].rstrip()


def parse_fields(entry):
    """Return [(name, value), ...] in source order, values brace-stripped."""
    fields = []
    i = entry.index(',', entry.index('{')) + 1
    while i < len(entry):
        m = re.compile(r'\s*([A-Za-z][\w-]*)\s*=\s*').match(entry, i)
        if not m:
            break
        name, j = m.group(1), m.end()
        if entry[j] == '{':
            depth = 0
            for k in range(j, len(entry)):
                if entry[k] == '{':
                    depth += 1
                elif entry[k] == '}':
                    depth -= 1
                    if depth == 0:
                        value, j = entry[j + 1:k], k + 1
                        break
            else:
                break
        elif entry[j] == '"':
            k = entry.index('"', j + 1)
            value, j = entry[j + 1:k], k + 1
        else:
            m2 = re.compile(r'([^,}\n]*)').match(entry, j)
            value, j = m2.group(1).strip(), m2.end()
        fields.append((name, value))
        i = entry.index(',', j) + 1 if ',' in entry[j:] else len(entry)
    return fields


def default_master(script_path):
    """Find allrefs.bib beside the script or one level up (scripts/ layout)."""
    here = os.path.dirname(os.path.abspath(script_path))
    for candidate in (os.path.join(here, 'allrefs.bib'),
                      os.path.join(here, os.pardir, 'allrefs.bib')):
        if os.path.isfile(candidate):
            return os.path.normpath(candidate)
    return None


def main():
    ap = argparse.ArgumentParser(
        description='Extract the references a .tex cites into a clean .bib.')
    ap.add_argument('tex', help='top-level .tex file')
    ap.add_argument('-o', '--out', help='output .bib (default: <stem>_refs.bib)')
    ap.add_argument('-m', '--master', help='master library .bib')
    args = ap.parse_args()

    master = args.master or default_master(__file__)
    if not master:
        sys.exit('error: could not locate allrefs.bib; pass --master')

    out = args.out or os.path.join(
        os.path.dirname(os.path.abspath(args.tex)),
        os.path.splitext(os.path.basename(args.tex))[0] + '_refs.bib')

    keys = cited_keys(args.tex)
    if not keys:
        sys.exit(f'error: no citations found in {args.tex}')

    library = open(master, encoding='utf-8').read()

    # BibTeX cite keys are case-insensitive, so the .tex may say Buchan1973a
    # while the library holds BUCHAN1973a. Match on lowercase to agree with
    # BibTeX rather than silently reporting the entry as missing.
    wanted = {k.lower(): k for k in keys}
    found, dropped, dup = {}, set(), []
    for key, typ, raw in split_entries(library):
        low = key.lower()
        if low not in wanted:
            continue
        if low in found:
            dup.append(key)
            continue
        names = [n.lower() for n, _ in parse_fields(raw)]
        dropped.update(n for n in names if n not in KEEP)
        kept = [(n, v) for n, v in parse_fields(raw) if n.lower() in KEEP]
        body = ',\n'.join(f'\t{n} = {{{v}}}' for n, v in kept)
        found[low] = f'@{typ}{{{key},\n{body}}}\n'

    with open(out, 'w', encoding='utf-8') as f:
        f.write('%% References cited by '
                f'{os.path.basename(args.tex)}.\n')
        f.write('%% Generated by bib_for_tex.py -- do not edit by hand.\n')
        f.write(f'%% Master library: {master}\n\n')
        for low in sorted(found, key=str.lower):
            f.write(found[low] + '\n')

    missing = [wanted[k] for k in wanted if k not in found]
    print(f'cited     : {len(keys)}')
    print(f'exported  : {len(found)} -> {out}')
    if dropped:
        print(f'fields cut: {", ".join(sorted(dropped))}')
    if dup:
        print(f'DUPLICATE : {", ".join(dup)}')
    if missing:
        print(f'MISSING   : {", ".join(sorted(missing))}')
    return 1 if missing or dup else 0


if __name__ == '__main__':
    sys.exit(main())
