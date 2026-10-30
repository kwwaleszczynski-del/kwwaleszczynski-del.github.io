"""Build the portfolio site (index.html, case studies, thumbnails) and the GitHub profile README.

The project list lives in projects.json; each entry points at a figure inside its own repository, which is
expected to be checked out next to this one (../<repo>/<image>). Thumbnails are fitted to 16:10 and saved as
WebP in img/, so both the site and the profile README load small images from GitHub Pages.

start_here.json holds the curated part: the "Start here" picks shown above the project groups and the case
studies, each written to case-studies/<repo>.html.

Usage:
    python build.py                                  # site + ../kwwaleszczynski-del/README.md
    python build.py --skip-images                    # text only, keep existing thumbnails and figures
    python build.py --profile-readme other/README.md
"""
import argparse
import html
import json
import logging
import re
import shutil
from datetime import date
from pathlib import Path

from PIL import Image, ImageSequence

log = logging.getLogger("build")

HERE = Path(__file__).resolve().parent
SITE_URL = "https://{user}.github.io/"
THUMB = (960, 600)

CSS = """:root {
  --bg: #f6f7f9; --card: #ffffff; --text: #151a22; --muted: #5a6474; --line: #e2e6ec; --chip: #edf0f4;
  --hl-bg: #fff8eb; --hl-line: #e8a33a; --pv: #c97a06; --wind: #0e7490; --storage: #6d43c9; --ops: #475569; --bio: #4d7c0f;
  --accent: #0e7490; --shadow: 0 1px 2px rgba(16,24,40,.06), 0 4px 16px rgba(16,24,40,.06);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117; --card: #151b24; --text: #e6eaf0; --muted: #98a2b3; --line: #252e3a; --chip: #1d2530;
    --hl-bg: #231d12; --hl-line: #d4912c; --pv: #f0a83a; --wind: #38bdd8; --storage: #a78bfa; --ops: #94a3b8; --bio: #9ccc65;
    --accent: #38bdd8; --shadow: none;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
a { color: inherit; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 20px; }
header.hero { padding: 64px 0 32px; }
.hero .name { font-size: 15px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }
.hero h1 { font-size: clamp(30px, 5vw, 48px); line-height: 1.1; margin: 0 0 16px; letter-spacing: -.02em; }
.hero h1 span { background: linear-gradient(90deg, var(--pv), var(--wind)); -webkit-background-clip: text;
  background-clip: text; color: transparent; }
.hero p.intro { max-width: 720px; font-size: 18px; color: var(--muted); margin: 0 0 24px; }
.stats { display: flex; flex-wrap: wrap; gap: 12px 32px; margin: 0 0 28px; padding: 0; list-style: none; }
.stats b { display: block; font-size: 28px; line-height: 1.1; }
.stats span { font-size: 14px; color: var(--muted); }
.actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { display: inline-block; padding: 7px 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--card);
  text-decoration: none; font-size: 14px; font-weight: 600; }
.btn:hover { border-color: var(--accent); }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
@media (prefers-color-scheme: dark) { .btn.primary { color: #06141a; } }
h2 { font-size: 22px; margin: 40px 0 16px; letter-spacing: -.01em; }
.lives { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.live { display: flex; gap: 12px; align-items: center; padding: 10px; background: var(--card); border: 1px solid var(--line);
  border-radius: 12px; text-decoration: none; font-weight: 600; box-shadow: var(--shadow); }
.live:hover { border-color: var(--accent); }
.live img { width: 96px; aspect-ratio: 16/10; object-fit: cover; border-radius: 6px; border: 1px solid var(--line); }
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }
.chip { font: inherit; font-size: 14px; padding: 6px 14px; border-radius: 999px; border: 1px solid var(--line);
  background: var(--chip); color: var(--text); cursor: pointer; }
.chip.active { background: var(--text); color: var(--bg); border-color: var(--text); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); gap: 20px; }
.card { display: flex; flex-direction: column; background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  overflow: hidden; box-shadow: var(--shadow); }
.card[hidden] { display: none; }
.thumb { display: block; border-bottom: 1px solid var(--line); background: #fff; }
.thumb img { display: block; width: 100%; height: auto; aspect-ratio: 16/10; object-fit: cover; }
.body { display: flex; flex-direction: column; flex: 1; padding: 16px 18px 18px; }
.meta { display: flex; gap: 8px; align-items: center; font-size: 13px; margin-bottom: 6px; }
.group { font-weight: 600; }
.group::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
  background: currentColor; vertical-align: 1px; }
.g-pv { color: var(--pv); } .g-wind { color: var(--wind); } .g-storage { color: var(--storage); } .g-ops { color: var(--ops); } .g-biogas { color: var(--bio); }
.badge { font-size: 12px; font-weight: 600; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--hl-line);
  color: var(--hl-line); }
.card h3 { font-size: 19px; line-height: 1.3; margin: 0 0 8px; }
.card h3 a { text-decoration: none; }
.card h3 a:hover { text-decoration: underline; }
.summary { margin: 0 0 12px; color: var(--muted); font-size: 15px; }
.highlight { margin: 0 0 14px; padding: 10px 12px; background: var(--hl-bg); border-left: 3px solid var(--hl-line);
  border-radius: 0 8px 8px 0; font-size: 15px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; list-style: none; padding: 0; margin: 0 0 16px; }
.tags li { font-size: 12px; padding: 2px 8px; border-radius: 6px; background: var(--chip); color: var(--muted); }
.links { display: flex; flex-wrap: wrap; gap: 8px; margin-top: auto; }
footer { margin: 56px 0 0; padding: 28px 0 48px; border-top: 1px solid var(--line); color: var(--muted); font-size: 14px; }
footer dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; margin: 0 0 16px; }
footer dt { font-weight: 600; color: var(--text); }
footer dd { margin: 0; }
.lead { max-width: 760px; color: var(--muted); margin: -4px 0 18px; }
.pick .owner { margin: 0 0 16px; font-size: 15px; }
.case { max-width: 800px; }
.crumb { margin: 28px 0 0; font-size: 14px; }
.crumb a { color: var(--muted); text-decoration: none; }
.crumb a:hover { color: var(--accent); }
.case header { padding: 28px 0 4px; }
.kicker { display: flex; gap: 8px; align-items: center; font-size: 13px; margin: 0 0 10px; }
.case h1 { font-size: clamp(28px, 4.4vw, 40px); line-height: 1.15; margin: 0 0 14px; letter-spacing: -.02em; }
.dek { font-size: 18px; color: var(--muted); margin: 0 0 24px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; list-style: none;
  padding: 0; margin: 0 0 28px; }
.kpis li { padding: 14px 16px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; box-shadow: var(--shadow); }
.kpis b { display: block; font-size: 24px; line-height: 1.2; margin-bottom: 4px; }
.kpis span { font-size: 14px; color: var(--muted); }
figure { margin: 0; }
figure img { display: block; width: 100%; height: auto; border: 1px solid var(--line); border-radius: 10px; background: #fff; }
figcaption { margin-top: 8px; font-size: 14px; color: var(--muted); }
.case h2 { font-size: 21px; margin: 36px 0 12px; }
.case section ul { margin: 0; padding-left: 20px; }
.case section li { margin: 0 0 10px; }
.case section > p { margin: 0 0 12px; }
.tablewrap { overflow-x: auto; margin: 18px 0 0; }
table { width: 100%; border-collapse: collapse; font-size: 14.5px; background: var(--card); }
caption { text-align: left; font-weight: 600; padding: 0 0 8px; }
th, td { padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
td + td, th + th { text-align: right; }
td + td { white-space: nowrap; }
.note { margin: 8px 0 0; font-size: 14px; color: var(--muted); }
.case .links { margin: 0 0 16px; }
@media (max-width: 560px) {
  .wrap { padding: 0 16px; }
  header.hero { padding-top: 40px; }
  .grid { grid-template-columns: 1fr; }
  footer dl { grid-template-columns: 1fr; }
  footer dd { margin-bottom: 8px; }
}
"""


def thumbnail(src: Path, dst: Path, anchor: str = "top", frame: float = 0.4, fit: str = "crop") -> None:
    """Fit an image (or one frame of a GIF) to 16:10 and save it as WebP."""
    with Image.open(src) as im:
        if getattr(im, "is_animated", False):
            frames = [f.copy() for f in ImageSequence.Iterator(im)]
            im = frames[int(frame * (len(frames) - 1))]
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, "white")
        im = Image.alpha_composite(bg, im).convert("RGB")
    w, h = im.size
    target = THUMB[0] / THUMB[1]
    if w / h > target:  # too wide: pad top and bottom, cropping the sides would cut chart axes
        new_h = round(w / target)
        padded = Image.new("RGB", (w, new_h), "white")
        padded.paste(im, (0, (new_h - h) // 2))
        im = padded
    elif fit == "pad":  # too tall, but a map should keep its edges: pad left and right
        new_w = round(h * target)
        padded = Image.new("RGB", (new_w, h), "white")
        padded.paste(im, ((new_w - w) // 2, 0))
        im = padded
    else:  # too tall: crop top/centre/bottom
        new_h = round(w / target)
        top = {"top": 0, "center": (h - new_h) // 2, "bottom": h - new_h}[anchor]
        im = im.crop((0, top, w, top + new_h))
    im = im.resize(THUMB, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=82, method=6)
    log.info("thumbnail %s (%d KB)", dst.name, dst.stat().st_size // 1024)


def e(text: str) -> str:
    return html.escape(text, quote=True)


def rich(text: str) -> str:
    # the only markup in start_here.json texts is **bold**
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e(text))


def thumb_src(p: dict) -> str:
    """Live preview published by the project itself if it has one, else the thumbnail built here."""
    return e(p.get("thumb_url") or f"img/{p['repo']}.webp")


def thumb_fallback(p: dict) -> str:
    # if the live preview is missing, fall back to the copy built from the project's figure
    return f" onerror=\"this.onerror=null;this.src='img/{p['repo']}.webp'\"" if p.get("thumb_url") else ""


def case_figure(c: dict) -> str:
    """Path of a case study figure relative to the site root: kept in this repository or copied into img/."""
    return c["image"][5:] if c["image"].startswith("site:") else f"img/case-{c['repo']}{Path(c['image']).suffix}"


def card(p: dict, user: str, groups: dict, cases: dict) -> str:
    repo_url = f"https://github.com/{user}/{p['repo']}"
    links = [f'<a class="btn" href="{repo_url}">Code</a>']
    if p["repo"] in cases:
        links.append(f'<a class="btn" href="case-studies/{p["repo"]}.html">Case study</a>')
    if p.get("demo"):
        links.append(f'<a class="btn primary" href="{e(p["demo"])}">{e(p.get("demo_label", "Live page"))} &#8599;</a>')
    badge = '<span class="badge">Own method</span>' if p.get("method") else ""
    tags = "".join(f"<li>{e(t)}</li>" for t in p.get("tags", []))
    return f"""
    <article class="card" data-group="{p['group']}" data-method="{'1' if p.get('method') else '0'}">
      <a class="thumb" href="{e(p.get('demo') or repo_url)}" tabindex="-1" aria-hidden="true">
        <img src="{thumb_src(p)}" alt="" loading="lazy" width="{THUMB[0]}" height="{THUMB[1]}"{thumb_fallback(p)}>
      </a>
      <div class="body">
        <div class="meta"><span class="group g-{p['group']}">{e(groups[p['group']])}</span>{badge}</div>
        <h3><a href="{repo_url}">{e(p['title'])}</a></h3>
        <p class="summary">{e(p['summary'])}</p>
        <p class="highlight">{e(p['highlight'])}</p>
        <ul class="tags">{tags}</ul>
        <div class="links">{''.join(links)}</div>
      </div>
    </article>"""


def pick(s: dict, p: dict, user: str, groups: dict, cases: dict) -> str:
    """A "Start here" card: the project, what it means for an asset owner, its case study first."""
    repo_url = f"https://github.com/{user}/{p['repo']}"
    links = []
    if p["repo"] in cases:
        links.append(f'<a class="btn primary" href="case-studies/{p["repo"]}.html">Case study</a>')
    if p.get("demo"):
        links.append(f'<a class="btn{"" if links else " primary"}" href="{e(p["demo"])}">'
                     f'{e(p.get("demo_label", "Live page"))} &#8599;</a>')
    links.append(f'<a class="btn" href="{repo_url}">Code</a>')
    badge = '<span class="badge">Case study</span>' if p["repo"] in cases else ""
    href = f"case-studies/{p['repo']}.html" if p["repo"] in cases else p.get("demo") or repo_url
    return f"""
    <article class="card pick">
      <a class="thumb" href="{e(href)}" tabindex="-1" aria-hidden="true">
        <img src="{thumb_src(p)}" alt="" loading="lazy" width="{THUMB[0]}" height="{THUMB[1]}"{thumb_fallback(p)}>
      </a>
      <div class="body">
        <div class="meta"><span class="group g-{p['group']}">{e(groups[p['group']])}</span>{badge}</div>
        <h3><a href="{e(href)}">{e(p['title'])}</a></h3>
        <p class="owner">{rich(s['for_owner'])}</p>
        <div class="links">{''.join(links)}</div>
      </div>
    </article>"""


def build_site(cfg: dict, start: dict) -> str:
    owner, projects = cfg["owner"], cfg["projects"]
    user = owner["github"]
    groups = {g["id"]: g["label"] for g in cfg["groups"]}
    by_repo = {p["repo"]: p for p in projects}
    cases = {c["repo"]: c for c in start["case_studies"]}
    demos = [p for p in projects if p.get("demo")]
    n_methods = sum(1 for p in projects if p.get("method"))
    chips = ['<button class="chip active" data-filter="all">All</button>']
    chips += [f'<button class="chip" data-filter="{gid}">{e(label)}</button>' for gid, label in groups.items()]
    chips.append('<button class="chip" data-filter="method">Own methods</button>')
    live = "".join(
        f'<a class="live" href="{e(p["demo"])}"><img src="{thumb_src(p)}" alt="" loading="lazy"{thumb_fallback(p)}>'
        f'<span>{e(p["title"])}</span></a>' for p in demos)
    picks = "".join(pick(s, by_repo[s["repo"]], user, groups, cases) for s in start["picks"])
    owner_links = "".join(f'<a class="btn" href="{e(l["url"])}">{e(l["label"])}</a>' for l in owner.get("links", []))
    name = owner.get("name") or user
    title = f"{name} | {owner['headline']}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(owner['intro'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(owner['intro'])}">
<meta property="og:image" content="{SITE_URL.format(user=user)}img/{projects[0]['repo']}.webp">
<meta name="color-scheme" content="light dark">
<style>
{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <p class="name">{e(name)}</p>
    <h1><span>{e(owner['headline'])}</span></h1>
    <p class="intro">{e(owner['intro'])}</p>
    <ul class="stats">
      <li><b>{len(projects)}</b><span>projects on open data</span></li>
      <li><b>{n_methods}</b><span>own verification methods</span></li>
      <li><b>{len(demos)}</b><span>live interactive pages</span></li>
    </ul>
    <div class="actions">
      <a class="btn primary" href="https://github.com/{user}">GitHub profile</a><a class="btn" href="#start">Start here &#8595;</a>{owner_links}
    </div>
  </header>

  <section id="start" aria-labelledby="start-h">
    <h2 id="start-h">Start here</h2>
    <p class="lead">{rich(start['intro'])}</p>
    <div class="grid">{picks}
    </div>
  </section>

  <section aria-labelledby="live-h">
    <h2 id="live-h">Live pages</h2>
    <div class="lives">{live}</div>
  </section>

  <section aria-labelledby="proj-h">
    <h2 id="proj-h">Projects</h2>
    <div class="filters" role="toolbar" aria-label="Filter projects">{''.join(chips)}</div>
    <div class="grid" id="projects">{''.join(card(p, user, groups, cases) for p in projects)}
    </div>
  </section>

  <footer>
    <dl>
      <dt>Stack</dt><dd>{e(' · '.join(cfg['stack']))}</dd>
      <dt>Open data</dt><dd>{e(' · '.join(cfg['data_sources']))}</dd>
    </dl>
    <p>All projects are personal work on public datasets, credited in each repository. Updated {date.today():%d %b %Y}.</p>
  </footer>
</div>
<script>
document.querySelectorAll(".chip").forEach(function (chip) {{
  chip.addEventListener("click", function () {{
    var f = chip.dataset.filter;
    document.querySelectorAll(".chip").forEach(function (c) {{ c.classList.toggle("active", c === chip); }});
    document.querySelectorAll("#projects .card").forEach(function (card) {{
      card.hidden = !(f === "all" || card.dataset.group === f || (f === "method" && card.dataset.method === "1"));
    }});
  }});
}});
</script>
</body>
</html>
"""


def build_case(c: dict, cfg: dict) -> str:
    """One case study page, written to case-studies/<repo>.html (links go one level up)."""
    owner = cfg["owner"]
    user = owner["github"]
    site = SITE_URL.format(user=user)
    groups = {g["id"]: g["label"] for g in cfg["groups"]}
    by_repo = {p["repo"]: p for p in cfg["projects"]}
    p = by_repo[c["repo"]]
    repo_url = f"https://github.com/{user}/{p['repo']}"
    name = owner.get("name") or user
    fig = case_figure(c)
    with Image.open(HERE / fig) as im:
        w, h = im.size
    bullets = lambda items: "".join(f"<li>{rich(t)}</li>" for t in items)  # noqa: E731
    t = c["table"]
    table = (f'<div class="tablewrap"><table><caption>{e(t["caption"])}</caption>'
             f'<thead><tr>{"".join(f"<th>{e(x)}</th>" for x in t["head"])}</tr></thead><tbody>'
             + "".join(f'<tr>{"".join(f"<td>{e(x)}</td>" for x in row)}</tr>' for row in t["rows"])
             + f'</tbody></table></div><p class="note">{e(t["note"])}</p>')
    kpis = "".join(f'<li><b>{e(k["value"])}</b><span>{e(k["label"])}</span></li>' for k in c["figures"])
    links = [f'<a class="btn" href="{repo_url}">Code and full results</a>']
    if p.get("demo"):
        links.append(f'<a class="btn primary" href="{e(p["demo"])}">{e(p.get("demo_label", "Live page"))} &#8599;</a>')
    related = "".join(f'<li><a href="https://github.com/{user}/{r}">{e(by_repo[r]["title"])}</a></li>'
                      for r in c["related"])
    title = f"{c['title']} | {name}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(c['dek'])}">
<meta property="og:title" content="{e(c['title'])}">
<meta property="og:description" content="{e(c['dek'])}">
<meta property="og:image" content="{site}{e(fig)}">
<meta name="color-scheme" content="light dark">
<style>
{CSS}</style>
</head>
<body>
<div class="wrap case">
  <p class="crumb"><a href="../#start">&#8592; {e(name)}: all projects</a></p>
  <header>
    <p class="kicker"><span class="group g-{p['group']}">{e(groups[p['group']])}</span><span class="badge">Case study</span></p>
    <h1>{e(c['title'])}</h1>
    <p class="dek">{rich(c['dek'])}</p>
    <ul class="kpis">{kpis}</ul>
  </header>
  <figure>
    <img src="../{e(fig)}" alt="{e(c['caption'])}" width="{w}" height="{h}">
    <figcaption>{e(c['caption'])}</figcaption>
  </figure>

  <section aria-labelledby="problem-h">
    <h2 id="problem-h">The problem</h2>
    {''.join(f"<p>{rich(t)}</p>" for t in c['problem'])}
  </section>

  <section aria-labelledby="method-h">
    <h2 id="method-h">Data and method</h2>
    <ul>{bullets(c['method'])}</ul>
  </section>

  <section aria-labelledby="result-h">
    <h2 id="result-h">Result</h2>
    <ul>{bullets(c['result'])}</ul>
    {table}
  </section>

  <section aria-labelledby="decision-h">
    <h2 id="decision-h">What it means for a decision</h2>
    <ul>{bullets(c['decision'])}</ul>
  </section>

  <section aria-labelledby="limits-h">
    <h2 id="limits-h">Limitations</h2>
    <ul>{bullets(c['limitations'])}</ul>
  </section>

  <section aria-labelledby="links-h">
    <h2 id="links-h">Links</h2>
    <div class="links">{''.join(links)}</div>
    <p>Related projects:</p>
    <ul>{related}</ul>
  </section>

  <footer>
    <p>Personal work on public data; the data sources are credited in the project's repository. Every number on
    this page is taken from the repository's README and result files. Updated {date.today():%d %b %Y}.</p>
  </footer>
</div>
</body>
</html>
"""


def build_profile(cfg: dict, start: dict) -> str:
    owner, projects = cfg["owner"], cfg["projects"]
    user = owner["github"]
    site = SITE_URL.format(user=user)
    groups = {g["id"]: g["label"] for g in cfg["groups"]}
    by_repo = {p["repo"]: p for p in projects}
    cases = {c["repo"] for c in start["case_studies"]}
    repo = lambda p: f"https://github.com/{user}/{p['repo']}"  # noqa: E731
    live = " · ".join(f"[{p['title']}]({p['demo']})" for p in projects if p.get("demo"))
    methods = " · ".join(f"[{p['title']}]({repo(p)})" for p in projects if p.get("method"))
    contact = " · ".join([f"[**Interactive Portfolio**]({site})"]
                         + [f"[**{l['label']}**]({l['url']})" for l in owner.get("links", [])])
    picks = []
    for s in start["picks"]:
        p = by_repo[s["repo"]]
        extra = f" · [case study]({site}case-studies/{p['repo']}.html)" if p["repo"] in cases else ""
        extra += f" · [{p.get('demo_label', 'Live page').lower()}]({p['demo']})" if p.get("demo") else ""
        picks.append(f"- **[{p['title']}]({repo(p)})**{extra}  \n  {s['for_owner']}")
    out = [f"### {owner['headline']}", "", contact, "", owner["intro"], "",
           "#### Start here", "", start["intro"], "", *picks, "",
           f"**Live pages:** {live}  ",
           f"**Own verification methods:** {methods}", ""]
    for gid, label in groups.items():
        items = [p for p in projects if p["group"] == gid]
        if not items:
            continue
        out += [f"#### {label}", "", "<table>"]
        for i in range(0, len(items), 2):
            out.append("<tr>")
            for p in items[i:i + 2]:
                demo = f' · <a href="{p["demo"]}">{p.get("demo_label", "Live page").lower()}</a>' if p.get("demo") else ""
                out.append(
                    f'<td width="50%" valign="top"><a href="{repo(p)}"><img src="{p.get("thumb_url") or site + "img/" + p["repo"] + ".webp"}" '
                    f'alt="{html.escape(p["title"])}"></a><br><b><a href="{repo(p)}">{html.escape(p["title"], quote=False)}</a></b>'
                    f'{demo}<br><sub>{html.escape(p["highlight"], quote=False)}</sub></td>')
            if len(items[i:i + 2]) == 1:
                out.append('<td width="50%"></td>')
            out.append("</tr>")
        out += ["</table>", ""]
    out += [f"**Stack:** {' · '.join(cfg['stack'])}  ", f"**Open data:** {' · '.join(cfg['data_sources'])}", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=HERE / "projects.json")
    ap.add_argument("--start", type=Path, default=HERE / "start_here.json", help="Start here picks and case studies")
    ap.add_argument("--repos-root", type=Path, default=HERE.parent, help="folder with the project repositories")
    ap.add_argument("--profile-readme", type=Path, default=HERE.parent / "kwwaleszczynski-del" / "README.md")
    ap.add_argument("--skip-images", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    start = json.loads(args.start.read_text(encoding="utf-8"))
    if not args.skip_images:
        for p in cfg["projects"]:
            # "site:" images live in this repository (e.g. a code card for a library without figures)
            src = HERE / p["image"][5:] if p["image"].startswith("site:") else args.repos_root / p["repo"] / p["image"]
            thumbnail(src, HERE / "img" / f"{p['repo']}.webp", p.get("anchor", "top"), p.get("frame", 0.4),
                      p.get("fit", "crop"))
        for c in start["case_studies"]:
            if not c["image"].startswith("site:"):  # case study figures are copied as they are, not cropped
                shutil.copyfile(args.repos_root / c["repo"] / c["image"], HERE / case_figure(c))
                log.info("figure %s", case_figure(c))
    (HERE / "index.html").write_text(build_site(cfg, start), encoding="utf-8")
    log.info("wrote index.html")
    (HERE / "case-studies").mkdir(exist_ok=True)
    for c in start["case_studies"]:
        (HERE / "case-studies" / f"{c['repo']}.html").write_text(build_case(c, cfg), encoding="utf-8")
        log.info("wrote case-studies/%s.html", c["repo"])
    args.profile_readme.parent.mkdir(parents=True, exist_ok=True)
    args.profile_readme.write_text(build_profile(cfg, start), encoding="utf-8")
    log.info("wrote %s", args.profile_readme)


if __name__ == "__main__":
    main()
