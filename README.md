# Swanson-Hysell Group references

This repo contains the master .bib file used by the Swanson-Hysell research group at UC Berkeley (http://www.swanson-hysell.org).

##Linking the bibliography with a paper in another repository

To use this file as the .bib file in a separate repository you can utilize Git's submodule functionality. Navigate to the repository with your paper in terminal and then create the submodule:

```
git submodule add https://github.com/swanson-hysell/references
```

A folder will be created that is the name of this repository. In your LaTeX file you can then refer to the allrefs.bib as a local reference: ```\bibliography{references/allrefs}```

If changes are made to the .bib file in this master repository (it should be changed here in this repo rather than in the repo with the manuscript) that you want to sync up in your project with the submodule. To do this, you can navigate to that repository and update the submodule with this command:

```
git submodule update --remote --merge
```

Hat tip to Andrius Velykis (https://github.com/andriusvelykis) for his blog post on this subject: http://andrius.velykis.lt/2012/06/master-bibtex-file-git-submodules/
