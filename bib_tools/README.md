# bib_tools

Utilities for working with the main BibTeX library, `allrefs.bib`.

## Per-project reference subsets

Entries in `allrefs.bib` are tagged with a `cited-by` field naming the projects
that cite them. A single entry can serve several projects:

```bibtex
@article{Tauxe2016a,
	author = {Tauxe, L. and Shaar, R. and Jonestrask, L. and ...},
	cited-by = {rockmagpy, bayesian_age_models},
	...
}
```

Each tag has a matching BibDesk smart group (`Cited-By` *contains* the tag),
stored in the `@comment{BibDesk Smart Groups{...}}` block at the end of
`allrefs.bib`, so the same subset can be browsed interactively in BibDesk.

`extract_tagged_refs.py` exports a tag as a standalone `.bib`:

```bash
python bib_tools/extract_tagged_refs.py rockmagpy
```

This writes `project_bibs/rockmagpy_refs.bib`. The main library is located
automatically by searching upward from the script, so the command works from
any directory. Running with an unrecognized tag lists the tags in use.

Exports strip the `bdsk-file-N` fields, which hold large base64 file bookmarks
that are meaningless outside BibDesk — the rockmagpy subset is 84 KB rather
than the 18 MB of the full library, which matters when syncing to Overleaf.
Pass `--keep-bdsk-files` to retain them when the export is destined for another
reference manager rather than for LaTeX.

## Checking a subset against a manuscript

The `cited-by` tags are maintained by hand and can drift from what a manuscript
actually cites. A LaTeX `.aux` file records the true citation list, so it can be
used to audit the tags:

```bash
python bib_tools/extract_tagged_refs.py rockmagpy \
    --check-aux ~/Dropbox/Writing/2026_RockmagPy/rockmagpy_paper/agujournaltemplate.aux
```

## Layout

```
references/
├── allrefs.bib          main library
├── bib_tools/           these utilities
└── project_bibs/        generated subsets (regenerate; do not hand-edit)
```
