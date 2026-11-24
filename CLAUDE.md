# references

Group master BibTeX file (`allrefs.bib`), maintained in BibDesk and used as a submodule in manuscript repos.

## Adding a reference
- Verify the entry against Crossref (DOI, authors, year, title, journal, pages) before adding it. Never add an entry you cannot verify.
- Add the entry near the top of `allrefs.bib`.
- Move the PDF into `~/Dropbox/Papers`, named `<CiteKey><Title truncated at a word boundary>.pdf`.
- Link it from the entry with a `bdsk-file-1` field: a base64 binary plist holding `relativePath = ../../Dropbox/Papers/<file>`.
- Pull with `git pull --rebase` before committing (see the README on avoiding conflicts in the .bib file).
