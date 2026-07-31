#!/usr/bin/env python3
"""Prepare a BibTeX library for upload by dropping unwanted fields.

Keeps every entry -- this is for the case where the whole library ships with the
manuscript -- but removes fields that are private to the reference manager or
simply never wanted in a reference list.

    python3 prepare_bib.py --drop bdsk-file,bdsk-url,month master.bib out.bib

Field names ending in a digit suffix (bdsk-file-1, bdsk-file-2, ...) are matched
by their stem, so `bdsk-file` covers all of them.
"""
import argparse
import re
import sys

# Values are either brace-delimited, quote-delimited, or a bare macro/number
# (e.g. `month = jun`). All three forms have to be recognised to be removed.
VALUE = r'(?:\{[^{}]*\}|"[^"]*"|[A-Za-z0-9]+)'


def build_pattern(fields):
    stems = '|'.join(re.escape(f) for f in fields)
    # The leading comma is consumed with the field, which correctly handles a
    # field in the middle of an entry as well as one that closes it.
    return re.compile(r',\s*(?:' + stems + r')(?:-\d+)?\s*=\s*' + VALUE,
                      re.IGNORECASE)


def count_fields(text, fields):
    stems = '|'.join(re.escape(f) for f in fields)
    return len(re.findall(r'^\s*(?:' + stems + r')(?:-\d+)?\s*=',
                          text, re.M | re.I))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--drop', required=True,
                    help='comma-separated field stems to remove')
    ap.add_argument('source')
    ap.add_argument('dest')
    args = ap.parse_args()

    fields = [f.strip() for f in args.drop.split(',') if f.strip()]
    text = open(args.source, encoding='utf-8').read()

    before_entries = len(re.findall(r'^@\w+\s*\{', text, re.M))
    before_fields = count_fields(text, fields)

    result = build_pattern(fields).sub('', text)

    after_entries = len(re.findall(r'^@\w+\s*\{', result, re.M))
    remaining = count_fields(result, fields)
    balanced = result.count('{') == result.count('}')

    open(args.dest, encoding='utf-8', mode='w').write(result)

    print(f'entries   : {before_entries} -> {after_entries}')
    print(f'fields cut: {before_fields - remaining} of {before_fields} '
          f'({", ".join(fields)})')
    print(f'remaining : {remaining}')
    print(f'size      : {len(text)/1e6:.2f} MB -> {len(result)/1e6:.2f} MB')
    print(f'balanced  : {balanced}')

    ok = (before_entries == after_entries) and remaining == 0 and balanced
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
