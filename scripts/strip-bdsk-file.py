#!/usr/bin/env python3
"""Git clean filter: drop BibDesk private fields from a .bib on the way into git.

BibDesk stores each linked PDF as a base64 macOS bookmark (`bdsk-file-N`) that
embeds the file's inode and volume metadata, so a cloud-sync tool rewriting the
PDF churns the blob even when nothing bibliographic has changed. `bdsk-url-N`
is likewise private bookkeeping that duplicates the `url`/`doi` fields.

Stripping both at the git boundary keeps BibDesk fully functional in the working
copy while giving git a stable, roughly half-size file to diff.

Install (per clone -- for security, git does not let a repository define its own
filters, so this cannot be committed and must be configured on each machine):

    git config filter.stripbdsk.clean "python3 /path/to/strip-bdsk-file.py"
    git config filter.stripbdsk.smudge cat
    echo '*.bib filter=stripbdsk' >> .gitattributes

The leading comma is consumed along with the field, which correctly handles both
a field in the middle of an entry and one that closes it.
"""
import re
import sys

DROP = re.compile(r',\s*bdsk-(?:file|url)-\d+\s*=\s*\{[^{}]*\}')


def strip(text):
    return DROP.sub('', text)


def main():
    sys.stdout.write(strip(sys.stdin.read()))


if __name__ == '__main__':
    main()
