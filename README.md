# kwwaleszczynski-del.github.io

Source of the portfolio page at **https://kwwaleszczynski-del.github.io/** and of the GitHub profile README.

Everything is generated from one file, `projects.json`: `build.py` crops a figure from each project repository
into a 16:10 WebP thumbnail (`img/`), writes the static `index.html` (no framework, no external requests) and
writes the profile README into the `kwwaleszczynski-del` repository checked out next to this one.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Pillow
.venv/Scripts/python build.py                             # site + ../kwwaleszczynski-del/README.md
.venv/Scripts/python build.py --skip-images               # text changes only
```

Adding a project means adding one entry to `projects.json` (repository, title, group, one-line summary, one
headline result, figure path, optional live page) and running the build.

Code: MIT. Figures belong to the projects they come from; data credits are in each project's README.
