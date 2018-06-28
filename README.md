# GitStats

This project exists to perform SLOC (Source Line of Code) counts on local git repositories and to break that information down by author. It accomplishes this by performing a recursive `git blame` on each source file in the repo.

## Example Uses:

To obtain SLOC-by-author stats on a particular repo:
```
python git_author_stats.py --repo /path/to/repo
```

To obtain SLOC-by-author stats for all modifications starting in 2017:
```
python git_author_stats.py --repo /path/to/repo --start-time 2017-01-01
```

To obtain SLOC-by-author stats for all modifications in 2016:
```
python git_author_stats.py --repo /path/to/repo --start-time 2016-01-01 --end-time 2017-01-01
```
