#!/usr/bin/env python3
"""Extract a subset of BibTeX entries from a master library by ``cited-by`` tag.

This reproduces, as a script, what a BibDesk smart group on the ``Cited-By``
field selects. Entries whose ``cited-by`` field contains the requested tag are
written to a new ``.bib`` file, optionally with the BibDesk ``bdsk-file-N``
base64 bookmark blobs stripped so that the result is small enough to sync
comfortably to Overleaf.

The workflow this supports is: tag entries in the master library with
``cited-by = {project_name}`` (a single entry can carry several
comma-separated tags), then export a per-project ``.bib`` on demand::

    python extract_tagged_refs.py rockmagpy
    python extract_tagged_refs.py rockmagpy rockmagpy_refs.bib
    python extract_tagged_refs.py bayesian_age_models --keep-bdsk-files

The master library is located automatically: ``allrefs.bib`` is looked for
beside this script and then in successive parent directories, so placing the
script in a subfolder of the references repository requires no configuration.
Use ``--bib`` to point at a library elsewhere.

Unless an output path is given, the exported ``.bib`` is written to a
``project_bibs`` folder alongside the master library, which keeps the generated
per-project subsets together and separate from the library itself.

The ``--check-aux`` option compares the tagged set against the citations LaTeX
actually emitted into an ``.aux`` file. The ``.aux`` is ground truth for a
manuscript: it reports keys that are cited but untagged (which would be missing
from the export, and which cause the script to exit non-zero) and keys that are
tagged but no longer cited.
"""

import argparse
import os
import re
import sys

LIBRARY_FILENAME = "allrefs.bib"

# Generated subsets are collected here, beside the master library.
OUTPUT_SUBDIR = "project_bibs"

# An entry header such as "@article{Tauxe2016a," at the start of a line.
ENTRY_HEADER = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)

# Entry types that carry no citation key and must be skipped.
NON_ENTRY_TYPES = {"comment", "preamble", "string"}


def locate_library(start_dir):
    """Search for the master ``.bib`` library from a directory upwards.

    Args:
        start_dir: Directory to begin the search in, typically the directory
            holding this script.

    Returns:
        Absolute path to the first ``allrefs.bib`` found, or None if the search
        reaches the filesystem root without finding one.
    """
    directory = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(directory, LIBRARY_FILENAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def find_entry_end(text, start):
    """Find the end of a BibTeX entry by matching its outermost braces.

    Brace matching is used rather than searching for the next ``@`` at the
    start of a line, because BibDesk appends an ``@comment{BibDesk Smart
    Groups{...}}`` block whose header does not match the entry pattern.

    Args:
        text: Full text of the ``.bib`` file.
        start: Index of the ``@`` that opens the entry.

    Returns:
        Index one past the entry's closing brace.

    Raises:
        ValueError: If the braces are unbalanced from ``start`` to end of file.
    """
    i = text.index("{", start)
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces in entry beginning at character %d" % start)


def parse_entries(text):
    """Split a ``.bib`` file into its individual entries.

    Args:
        text: Full text of the ``.bib`` file.

    Returns:
        List of ``(key, entry_text)`` tuples in file order, excluding
        ``@comment``, ``@preamble``, and ``@string`` blocks.
    """
    entries = []
    for match in ENTRY_HEADER.finditer(text):
        entry_type, key = match.group(1).lower(), match.group(2)
        if entry_type in NON_ENTRY_TYPES:
            continue
        end = find_entry_end(text, match.start())
        entries.append((key, text[match.start():end]))
    return entries


def get_tags(entry):
    """Return the comma-separated values of an entry's ``cited-by`` field.

    Args:
        entry: Text of a single BibTeX entry.

    Returns:
        List of tag strings, lowercased and stripped; empty if the entry has no
        ``cited-by`` field.
    """
    match = re.search(r"^\s*cited-by = \{([^}]*)\}", entry, re.M | re.I)
    if not match:
        return []
    return [tag.strip().lower() for tag in match.group(1).split(",") if tag.strip()]


def strip_bdsk_files(entry, key):
    """Remove ``bdsk-file-N`` fields, which hold large base64 file bookmarks.

    The ``bdsk-url-N`` fields are kept, as they are short and useful. If the
    removed field was the last one in the entry, the preceding field's trailing
    comma is converted back into the entry's closing brace.

    Args:
        entry: Text of a single BibTeX entry.
        key: Citation key, used only in error messages.

    Returns:
        The entry text with ``bdsk-file-N`` fields removed.

    Raises:
        ValueError: If the entry does not end in the expected ``}}``.
    """
    kept = [line for line in entry.split("\n")
            if not re.match(r"^\s*bdsk-file-\d+ = ", line, re.I)]
    body = "\n".join(kept).rstrip()
    if body.endswith("}}"):
        return body
    if not body.endswith(","):
        raise ValueError("unexpected entry structure for %s after stripping "
                         "bdsk-file fields" % key)
    return body[:-1] + "}"


def read_aux_citations(aux_path):
    """Read the citation keys LaTeX recorded in an ``.aux`` file.

    Args:
        aux_path: Path to the ``.aux`` file produced by a LaTeX run.

    Returns:
        Set of citation keys appearing in ``\\citation{}`` records. Keys can be
        comma-separated within a single record, and ``\\citation{*}`` (emitted
        by ``\\nocite{*}``) is ignored.
    """
    keys = set()
    with open(aux_path, encoding="utf-8", errors="replace") as aux_file:
        for line in aux_file:
            match = re.match(r"\\citation\{(.+)\}\s*$", line)
            if match:
                keys.update(k.strip() for k in match.group(1).split(",")
                            if k.strip() and k.strip() != "*")
    return keys


def main():
    parser = argparse.ArgumentParser(
        description="Extract BibTeX entries carrying a given cited-by tag, "
                    "reproducing a BibDesk smart group as a .bib file.")
    parser.add_argument("tag",
                        help="cited-by tag to select on, matched "
                             "case-insensitively (e.g. rockmagpy)")
    parser.add_argument("output", nargs="?",
                        help="path of the .bib file to write (default: "
                             "<tag>_refs.bib in the %s folder beside the master "
                             "library)" % OUTPUT_SUBDIR)
    parser.add_argument("--bib",
                        help="master .bib library to read (default: the nearest "
                             "%s found beside this script or in a parent "
                             "directory)" % LIBRARY_FILENAME)
    parser.add_argument("--keep-bdsk-files", action="store_true",
                        help="retain the bdsk-file-N base64 bookmark blobs, "
                             "which makes the output much larger")
    parser.add_argument("--check-aux", metavar="AUX",
                        help="compare the tagged set against the citations in a "
                             "LaTeX .aux file and report any disagreement")
    args = parser.parse_args()

    bib_path = args.bib or locate_library(os.path.dirname(os.path.abspath(__file__)))
    if not bib_path:
        sys.exit("Could not find %s beside this script or in any parent "
                 "directory. Pass --bib with an explicit path."
                 % LIBRARY_FILENAME)
    if not os.path.isfile(bib_path):
        sys.exit("No such .bib library: %s" % bib_path)

    if args.output:
        output_path = args.output
    else:
        output_dir = os.path.join(os.path.dirname(bib_path), OUTPUT_SUBDIR)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "%s_refs.bib" % args.tag)

    with open(bib_path, encoding="utf-8", errors="replace") as bib_file:
        text = bib_file.read()

    entries = parse_entries(text)
    tag = args.tag.lower()
    selected = [(key, entry) for key, entry in entries if tag in get_tags(entry)]

    if not selected:
        all_tags = sorted({t for _, entry in entries for t in get_tags(entry)})
        sys.exit("No entries in %s carry cited-by = {%s}.%s"
                 % (bib_path, args.tag,
                    ("\nTags present in this library: %s" % ", ".join(all_tags))
                    if all_tags else ""))

    keys = [key for key, _ in selected]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        print("Warning: duplicate citation keys in the tagged set: %s"
              % ", ".join(duplicates), file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write("%% References tagged cited-by = {%s} in %s.\n"
                       "%% Generated by extract_tagged_refs.py -- do not edit "
                       "by hand.\n\n" % (args.tag, os.path.basename(bib_path)))
        for key, entry in sorted(selected, key=lambda pair: pair[0].lower()):
            if not args.keep_bdsk_files:
                entry = strip_bdsk_files(entry, key)
            out_file.write(entry.rstrip() + "\n\n")

    print("Wrote %d entries tagged '%s' from %s to %s (%.0f KB)."
          % (len(selected), args.tag, os.path.basename(bib_path), output_path,
             os.path.getsize(output_path) / 1024))

    if args.check_aux:
        cited = read_aux_citations(args.check_aux)
        tagged = set(keys)
        untagged = sorted(cited - tagged)
        unused = sorted(tagged - cited)
        aux_name = os.path.basename(args.check_aux)
        if untagged:
            print("\nCited in %s but NOT tagged '%s' (missing from the export):"
                  % (aux_name, args.tag))
            for key in untagged:
                print("  %s" % key)
        if unused:
            print("\nTagged '%s' but not cited in %s (harmless, just extra):"
                  % (args.tag, aux_name))
            for key in unused:
                print("  %s" % key)
        if not untagged and not unused:
            print("\nTagged set matches the citations in %s exactly." % aux_name)
        if untagged:
            sys.exit(1)


if __name__ == "__main__":
    main()
