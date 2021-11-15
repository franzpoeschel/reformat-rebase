# reformat-rebase

This little tool helps Git-based projects to start using automatic formatting tools.
When such automatic formatting is applied to an entire code base, it is usually difficult to bring old pull requests up to speed.

## Workflow

In the first step, users should manually rebase their feature branch onto the last commit that is not yet formatted.
The result should look like this:

```
                     (f1) (f2) (f3)
feature branch     –––*––––*––––*–––
                 /
dev branch *––––*–––––––––––––––––––––*–––
                |                     |
           last commit     commit that reformats
         before reformat        the code base
              (dev1)               (dev2)
```

The feature branch should be checked out, the last commit before reformat (`(dev1)` in the chart) should be passed (e.g. as a commit hash) via `--old-base`.
Additionally, you need to provide a command via `--reformat` that `reformat-rebase` can use (via `subprocess.call()`) to manually reformat the entire codebase.
`reformat-rebase` will then create a new temporary feature branch (name specified via `--new-branch`) based on commit `(dev1)`.
On this branch, `reformat-rebase` will:

* First create a (temporary) commit by applying the reformatting command.
* Then reapply each commit on the feature branch, reformatting each single commit.
  For each reapplied commit `(c)`, the script will:

  1. Reapply the commit by calling `git checkout (c) -- .`.
  2. Reformat the commit by using the supplied script.
  3. Commit the changes by using the same commit message.

The result of this procedure should look like this:
```
                    temporary
                     reformat
                      commit  (f1') (f2') (f3')
                         |      |     |     |
temporary branch      –––*––––––*–––~–*–~–––*–––
                    /
                   / (f1) (f2) (f3)
feature branch     –––*––––*––––*–––
                 /
dev branch *––––*–––––––––––––––––––––*–––
                |                     |
           last commit     commit that reformats
         before reformat        the code base
              (dev1)               (dev2)
```

The temporary reformat commit should then have roughly similar contents compared to `(dev2)`.
(There might be slight differences, because `(dev2)` might e.g. have introduced changes to CI workflows.)

So, there should now be few conflicts (ideally none at all) when rebasing the temporary branch upon `(dev2)` (leaving out the temporary commit).
This script informs you about the necessary `git rebase` command, but it should look roughly like:
```bash
git rebase --onto (dev2) "<temporary reformat commit>"
```
Since there might be merge conflicts that need to be resolved manually, you will need to do that step manually.
After rebasing:
```


                                            (f1') (f2') (f3')
                                              |     |     |
temporary branch                           –––*–––~–*–~–––*–––
                                          /
                     (f1) (f2) (f3)      /
feature branch     –––*––––*––––*–––    /
                 /                     /
dev branch *––––*–––––––––––––––––––––*–––
                |                     |
           last commit     commit that reformats
         before reformat        the code base
              (dev1)               (dev2)
```

Finally, if everything went fine, you can update your feature branch to the temporary branch:
```bash
git checkout "<feature-branch>"
git reset --hard "<temporary-branch>"
```
Be aware of the typical consequences of `git reset --hard`.

## Caveats

This is (currently) a quick-n-dirty script and things might go south.
Please be sure to understand how it works before running it.
It tries to avoid damage by creating a new branch, but standard caution applies.

* This script interacts with `git` by using its command line interface via `subprocess.call()` and `subprocess.getstatusoutput()`.
  This has been tested on Linux (Ubuntu 21.04).
  Be aware that this approach implies lots of string output parsing.
* This script uses `git rev-list` to get the list of commits to be reapplied.
  Be aware of this when dealing with merging branches.
* Author information is currently lost when reapplying commits.
  Commits are currently reapplied by copying the commit mesasge and nothing more.
* The command passed via `--reformat` is called with `subprocess.call()` in Python.
  If you put the commands for reformatting inside a script `./reformat.sh`, this means that you need to be explicit about the interpreter, e.g.: `reformat-rebase --reformat bash ./reformat.sh …`.
* If any command returns a non-zero return code, the script will exit with an exception and leave the temporary branch in its current status.
