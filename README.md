# Swanson-Hysell Group references

This repository contains the master .bib file used by the Swanson-Hysell research group at UC Berkeley (http://www.swanson-hysell.org).

## Linking the bibliography with a paper in another repository

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

## Avoiding conflicts

Adding references to the main .bib file within the BibTeX framework results in the generation of extraneous text (outside of the simple appending of the new reference to the existing file). This means that collaborative use of this shared .bib file will inevitably result in conflicts that are not always straightforward to resolve manually.  

The best way to avoid these conflicts requires a slightly more involved but overall less annoying method of syncing changes (new references) to the master .bib file. From what I can tell, the ```git rebase``` command (as opposed to the more common ```git merge```) allows for local changes to be "replayed" on top of the most recent changes to the master. This contrasts with ```git merge``` or ```git push```, which inevitably result in a conflict when confronted with a .bib file
formatted for different users (even if the bibliography is exactly the same). 

***Note: It's possible that*** `git merge` ***would also be sufficient for our purposes and I'm just overcomplicating things. Maybe the key is just to make changes within branches (see workflow below).***

If you would like to try this approach, the general workflow is as follows:

* Make any changes as you would normally within the BibTeX app
* Once you're ready to sync those changes to the GitHub repository, navigate to the ```references``` directory on the command line.
* If you enter ```git status```, you should get the notification that you have unstaged changes (nothing has been added/"staged" or committed yet).
* Run the following commands:

  1. Move changes into a separate branch and commit them
  
    ```
    git checkout -b <name-of-your-branch>
    git add -A
    git commit -a -m "your commit message"
    ```
  2. Move back to master branch and sync the current version
  
    ```
    git checkout master # move back to master branch and sync current version
    git pull
    ```
  3. Rebase: replay your changes on top of any recent changes to the master
  
    ```
    git checkout <name-of-your-branch>
    git rebase master
    ```
  3. Sync your changes to GitHub
  
    ```
    git checkout master
    git merge <name-of-your-branch>
    git push
    ```
