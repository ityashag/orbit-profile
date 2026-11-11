#!/usr/bin/env python3
"""Builds an animated GitHub profile README from your live pull requests.

Run it in your profile repo (the one named after your username):

    GH_TOKEN=<token> python3 build.py

It writes README.md, assets/cover.svg and assets/receipt.svg. Every number comes
from the GitHub API at build time. Settings live in profile.json; all are optional.
Needs only Python 3.9+, no packages.
"""
import datetime as dt
import html
import json
import math
import os
import pathlib
import random
import re
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
CONFIG_PATH = pathlib.Path(os.environ.get("ORBIT_CONFIG", ROOT / "profile.json"))
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf8")) if CONFIG_PATH.exists() else {}


def token():
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(name):
            return os.environ[name]
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("No GitHub token: set GH_TOKEN (or GITHUB_TOKEN), or log in with the GitHub CLI.")


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "orbit-profile"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    if out.get("errors"):
        sys.exit(f"GitHub API error: {out['errors'][0].get('message')}")
    return out["data"]


TOKEN = token()
LOGIN = (sys.argv[1] if len(sys.argv) > 1 else None) or CONFIG.get("login") or os.environ.get("GITHUB_REPOSITORY_OWNER")
if not LOGIN:
    sys.exit('Which account? Set "login" in profile.json or pass it: python3 build.py <username>')
MIN_STARS = int(CONFIG.get("min_stars", 1000))
MAX_PRS = int(CONFIG.get("max_prs", 300))

user = gql("""query($login:String!){user(login:$login){name createdAt
  repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,orderBy:{field:PUSHED_AT,direction:DESC}){
    totalCount nodes{name isFork url primaryLanguage{name}}}}}""", {"login": LOGIN})["user"]
if user is None:
    sys.exit(f"No GitHub user called {LOGIN!r}.")
prs, cursor = [], None
while len(prs) < MAX_PRS:
    page = gql("""query($login:String!,$after:String){user(login:$login){
      pullRequests(first:50,after:$after,orderBy:{field:CREATED_AT,direction:DESC}){
        pageInfo{hasNextPage endCursor}
        nodes{number title url state merged additions deletions body
          repository{nameWithOwner stargazerCount isPrivate owner{login}}
          files(first:100){nodes{path additions deletions}}}}}}""", {"login": LOGIN, "after": cursor})["user"]["pullRequests"]
    prs += page["nodes"]
    if not page["pageInfo"]["hasNextPage"]:
        break
    cursor = page["pageInfo"]["endCursor"]
prs = [p for p in prs[:MAX_PRS] if not p["repository"]["isPrivate"] and p["state"] != "CLOSED" or p["merged"]]

NAME = CONFIG.get("name") or user["name"] or LOGIN
TAGLINE = CONFIG.get("tagline", "contributing to open source, one small PR at a time")
PROJECT_NAMES = CONFIG.get("project_names", {})
now = dt.datetime.now(dt.timezone.utc)
repos = user["repositories"]["nodes"]
original = [r for r in repos if not r["isFork"]]
external = [p for p in prs if p["repository"]["owner"]["login"].lower() != LOGIN.lower()]
oss = [p for p in external if p["repository"]["stargazerCount"] >= MIN_STARS]
team = [p for p in external if p["repository"]["stargazerCount"] < MIN_STARS]
oss_projects = {p["repository"]["nameWithOwner"]: p["repository"]["stargazerCount"] for p in oss}
stars_combined = sum(oss_projects.values())
oss_merged = sum(p["merged"] for p in oss)
oss_open = sum(p["state"] == "OPEN" for p in oss)
added = sum(p["additions"] for p in oss)
removed = sum(p["deletions"] for p in oss)
languages = {}
for r in original:
    if r["primaryLanguage"]:
        languages[r["primaryLanguage"]["name"]] = languages.get(r["primaryLanguage"]["name"], 0) + 1
top_languages = [k for k, _ in sorted(languages.items(), key=lambda kv: (-kv[1], kv[0])) if k != "Jupyter Notebook"][:3]
repo_by_name = {r["name"]: r for r in repos}
today = f"{now.day} {now.strftime('%b %Y')}"
since = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00")).strftime("%b %Y")


def esc(s):
    return html.escape(str(s), quote=True)


def project(repo):
    return PROJECT_NAMES.get(repo, repo.split("/")[1])


# ---------------------------------------------------------------- cosmos
SANS = "ui-sans-serif,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"
SPACE, STAR, SOFT, MERGED, PAPER, INK, FAINT = "#04050A", "#F4F1E8", "#9CA0A8", "#3FB950", "#F5F2E9", "#22211E", "#6F6D66"
STYLE = """<style>
.tw{animation:tw var(--d) ease-in-out infinite;animation-delay:var(--o)}
@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}
.sp{transform-box:view-box;transform-origin:var(--c);animation:sp var(--d) linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
.bob{animation:bob 11s ease-in-out infinite alternate}
@keyframes bob{from{transform:translateY(-5px)}to{transform:translateY(5px)}}
.draw{stroke-dasharray:var(--l);stroke-dashoffset:var(--l);animation:draw 1.1s ease-out forwards;animation-delay:var(--o)}
@keyframes draw{to{stroke-dashoffset:0}}
.rise{opacity:0;animation:rise .9s ease-out forwards;animation-delay:var(--o)}
@keyframes rise{to{opacity:1}}
.pulse{transform-box:fill-box;transform-origin:center;opacity:0;animation:pulse 3.6s ease-out infinite;animation-delay:var(--o)}
@keyframes pulse{0%{transform:scale(.7);opacity:.5}100%{transform:scale(2.8);opacity:0}}
.meteor{opacity:0;animation:meteor var(--d) linear infinite;animation-delay:var(--o)}
@keyframes meteor{0%{transform:translate(0,0);opacity:0}1.5%{opacity:.9}7%{transform:translate(-300px,150px);opacity:0}100%{transform:translate(-300px,150px);opacity:0}}
@media (prefers-reduced-motion:reduce){.tw,.sp,.bob,.pulse,.meteor{animation:none}.draw{animation:none;stroke-dashoffset:0}.rise{animation:none;opacity:1}}
</style>"""

# The conventional-commit type in a PR title, as a kind of work.
KINDS = {"fix": "Bug fixes", "docs": "Docs", "test": "Tests", "feat": "Features", "perf": "Performance",
         "chore": "Cleanup", "refactor": "Cleanup", "style": "Cleanup", "ci": "Build and CI", "build": "Build and CI"}
LANGS = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
         ".go": "Go", ".java": "Java", ".kt": "Kotlin", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
         ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".swift": "Swift", ".scala": "Scala",
         ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte", ".css": "CSS", ".scss": "CSS", ".html": "HTML",
         ".sh": "Shell", ".json": "JSON", ".yml": "YAML", ".yaml": "YAML", ".md": "Markdown", ".mdx": "Markdown"}
CODE_EXT = tuple(ext for ext, lang in LANGS.items() if lang not in ("JSON", "YAML", "Markdown"))
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|visual)/|(^|/)src/test/|_test\.(go|py)$|\.(test|spec)\.[jt]sx?$"
                       r"|(^|/)test_[^/]+\.py$|Tests?\.(java|kt|cs)$|_spec\.rb$")
# Areas of a codebase by path prefix, from profile.json; the first match wins.
AREAS = {repo: [tuple(pair) for pair in pairs] for repo, pairs in CONFIG.get("areas", {}).items()}


# For titles without a conventional-commit type: the first word, after any issue key.
VERBS = (("fix", "Bug fixes"), ("correct", "Bug fixes"), ("prevent", "Bug fixes"), ("avoid", "Bug fixes"),
         ("handle", "Bug fixes"), ("add", "Features"), ("support", "Features"), ("implement", "Features"),
         ("introduce", "Features"), ("allow", "Features"), ("enable", "Features"), ("doc", "Docs"),
         ("readme", "Docs"), ("test", "Tests"), ("refactor", "Cleanup"), ("remove", "Cleanup"),
         ("clean", "Cleanup"), ("rename", "Cleanup"), ("simplify", "Cleanup"), ("bump", "Dependencies"),
         ("upgrade", "Dependencies"), ("speed", "Performance"), ("optimi", "Performance"))


def kind(p):
    m = re.match(r"(\w+)(\([^)]*\))?!?:", p["title"])
    if m and m.group(1).lower() in KINDS:
        return KINDS[m.group(1).lower()]
    title = re.sub(r"^(\[[^\]]*\]\s*|[A-Z][A-Z0-9]+-\d+\s*[:\-]?\s*|\w+(\([^)]*\))?!?:\s*)+", "", p["title"]).lower()
    return next((k for word, k in VERBS if title.startswith(word)), "Other changes")


def files(p):
    return (p.get("files") or {}).get("nodes") or []


def area_of(repo, path):
    for prefix, name in AREAS.get(repo, []):
        if path.startswith(prefix):
            return name
    return path.split("/")[0] if "/" in path else project(repo)


def main_area(p):
    """Where most of a PR's non-test lines went."""
    repo = p["repository"]["nameWithOwner"]
    changed = [f for f in files(p) if not TEST_PATH.search(f["path"])] or files(p)
    weight = {}
    for f in changed:
        a = area_of(repo, f["path"])
        weight[a] = weight.get(a, 0) + f["additions"] + f["deletions"]
    return max(weight, key=weight.get) if weight else project(repo)


def is_code_fix(p):
    return kind(p) == "Bug fixes" and any(f["path"].endswith(CODE_EXT) and not f["path"].startswith("docs/") for f in files(p))


def has_tests(p):
    return any(TEST_PATH.search(f["path"]) for f in files(p))


def language_share(items):
    """Each language's share of the lines changed, largest first."""
    lines = {}
    for p in items:
        for f in files(p):
            lang = LANGS.get(pathlib.PurePosixPath(f["path"]).suffix.lower())
            if lang:
                lines[lang] = lines.get(lang, 0) + f["additions"] + f["deletions"]
    total = sum(lines.values()) or 1
    return [(lang, round(100 * n / total)) for lang, n in sorted(lines.items(), key=lambda kv: -kv[1])]


def summary():
    """Everything the receipt and README say about the work, from the PRs themselves."""
    by_project, kinds, areas = {}, {}, {}
    for p in oss:
        by_project.setdefault(project(p["repository"]["nameWithOwner"]), []).append(p)
        kinds[kind(p)] = kinds.get(kind(p), 0) + 1
        areas.setdefault((project(p["repository"]["nameWithOwner"]), main_area(p)), []).append(p)
    code_fixes = [p for p in oss if is_code_fix(p)]
    return {
        "projects": sorted(by_project.items(), key=lambda kv: -len(kv[1])),
        "kinds": sorted(kinds.items(), key=lambda kv: -kv[1]),
        "code_fixes": code_fixes,
        "tested": sum(has_tests(p) for p in code_fixes),
        "areas": sorted(areas.items(), key=lambda kv: (-len(kv[1]), kv[0])),
        "langs": language_share(oss),
    }


SM = summary()


def starfield(w, h, seed, count=170):
    """Mostly fixed stars, a few twinkling, over a faint band of the Milky Way."""
    rng = random.Random(seed)
    out = ['<defs><radialGradient id="mw"><stop offset="0" stop-color="#C9C4B8" stop-opacity=".13"/>'
           '<stop offset=".55" stop-color="#8E8F9E" stop-opacity=".05"/><stop offset="1" stop-color="#8E8F9E" stop-opacity="0"/></radialGradient></defs>',
           f'<rect width="{w}" height="{h}" fill="{SPACE}"/>',
           f'<ellipse cx="{w * .6}" cy="{h * .45}" rx="{w * .62}" ry="{h * .34}" fill="url(#mw)" transform="rotate(-18 {w * .6} {h * .45})"/>']
    for i in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice((.5, .6, .7, .8, .9, 1.1, 1.5))
        col = rng.choice((STAR, STAR, STAR, "#CFE0FF", "#FFE2C2"))
        if i % 7 == 0:
            out.append(f'<circle class="tw" style="--d:{rng.uniform(3, 8):.1f}s;--o:-{rng.uniform(0, 8):.1f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"/>')
        else:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}" opacity="{rng.uniform(.25, .85):.2f}"/>')
    return "".join(out)


def star_trails(px, py, seed, count=340, reach=1150):
    rng = random.Random(seed)
    arcs = []
    for _ in range(count):
        r = (rng.random() ** .72) * reach + 18
        start = rng.uniform(0, 360)
        a0, a1 = math.radians(start), math.radians(start + rng.uniform(12, 34))
        x0, y0 = px + r * math.cos(a0), py + r * math.sin(a0)
        x1, y1 = px + r * math.cos(a1), py + r * math.sin(a1)
        col = rng.choice((STAR, STAR, STAR, "#BFD4FF", "#FFD9B0"))
        arcs.append(f'<path d="M{x0:.0f},{y0:.0f} A{r:.0f},{r:.0f} 0 0,1 {x1:.0f},{y1:.0f}" stroke="{col}" stroke-opacity="{rng.uniform(.28, .95):.2f}" stroke-width="{rng.choice((.8, 1, 1.3, 1.7))}"/>')
    return f'<g class="sp" fill="none" stroke-linecap="round" style="--d:170s;--c:{px}px {py}px">{"".join(arcs)}</g>'


def cover():
    """Your name over a turning star-trail sky, with your latest PRs as a constellation."""
    w, h = 1280, 440
    px, py = 930, 200
    fade = ('<defs><linearGradient id="left"><stop offset="0" stop-color="#04050A" stop-opacity=".96"/>'
            '<stop offset=".44" stop-color="#04050A" stop-opacity=".74"/><stop offset=".72" stop-color="#04050A" stop-opacity="0"/></linearGradient></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#left)"/>')
    text = (f'<text x="72" y="218" font-family="{SERIF}" font-size="80" fill="{STAR}">{esc(NAME)}</text>'
            f'<text x="75" y="264" font-family="{SERIF}" font-style="italic" font-size="27" fill="{SOFT}">{esc(TAGLINE)}</text>')
    names = list(dict.fromkeys(project(p["repository"]["nameWithOwner"]) for p in oss))
    if oss:
        shown = ", ".join(names[:4]) + (f" and {len(names) - 4} more" if len(names) > 4 else "")
        text += f'<text x="76" y="306" font-family="{MONO}" font-size="16" fill="{SOFT}">{oss_merged} merged · {oss_open} open · {esc(shown)}</text>'
    points = [(792, 96), (926, 58), (1032, 158), (884, 246), (1006, 338)]
    rows = oss[:5]
    pts = points[:len(rows)]
    lines = "".join(
        f'<path class="draw" style="--l:{math.dist(a, b):.0f};--o:{.6 + i * .7:.1f}s" d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="{STAR}" stroke-opacity=".5" stroke-width="1"/>'
        for i, (a, b) in enumerate(zip(pts, pts[1:])))
    stars = []
    for i, ((x, y), p) in enumerate(zip(pts, rows)):
        col = MERGED if p["merged"] else STAR
        repo = p["repository"]["nameWithOwner"].split("/")[1]
        ring = (f'<circle class="pulse" style="--o:{2 + i * .9:.1f}s" cx="{x}" cy="{y}" r="9" fill="none" stroke="{MERGED}" stroke-width="1.5"/>'
                if p["merged"] else "")
        stars.append(f'<g class="rise" style="--o:{.2 + i * .7:.1f}s">{ring}<circle cx="{x}" cy="{y}" r="11" fill="{col}" opacity=".16"/><circle class="tw" style="--d:{5 + (p["number"] % 4)}s;--o:-{p["number"] % 5}s" cx="{x}" cy="{y}" r="5.5" fill="{col}"/>'
                     f'<text x="{x + 17}" y="{y + 1}" font-family="{MONO}" font-size="16" fill="{STAR}">{esc(repo)} #{p["number"]}</text>'
                     f'<text x="{x + 17}" y="{y + 20}" font-family="{SERIF}" font-style="italic" font-size="15" fill="{col if p["merged"] else SOFT}">{"merged" if p["merged"] else "open"}</text></g>')
    meteors = "".join(
        f'<line class="meteor" style="--d:{d}s;--o:{o}s" x1="{x}" y1="{y}" x2="{x + 46}" y2="{y - 23}" stroke="{STAR}" stroke-width="1.3" stroke-linecap="round"/>'
        for x, y, d, o in ((640, 40, 11, 3), (520, 120, 17, 9)))
    label = f"{NAME}, over a slow star-trail sky. A constellation marks {len(rows)} real pull requests: {oss_open} open and {oss_merged} merged."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'{STYLE}<rect width="{w}" height="{h}" fill="{SPACE}"/>{star_trails(px, py, 41)}{fade}{meteors}{text}{lines}{"".join(stars)}</svg>')


def orrery(cx, cy):
    """One orbit per project, one moon per pull request; the busiest project gets the widest orbit."""
    groups = {}
    for p in oss:
        groups.setdefault(p["repository"]["nameWithOwner"], []).append(p)
    # Three orbits at most: more would crowd the moons and stack the names.
    ranked = sorted(groups.items(), key=lambda kv: (len(kv[1]), kv[0]))
    rings, hidden = ranked[-3:], len(ranked[:-3])
    if not rings:
        return []
    radii = [58 + i * 46 for i in range(len(rings))]
    # One moon size for every orbit, shrinking only when the widest one fills up.
    moon = min(6.0, max(2.5, 2 * math.pi * radii[-1] / max(len(i) for _, i in rings) / 3.2))
    out = [f'<circle cx="{cx}" cy="{cy}" r="9" fill="#FFE2C2"/><circle cx="{cx}" cy="{cy}" r="20" fill="#FFE2C2" opacity=".12"/>']
    for i, ((repo, items), r) in enumerate(zip(rings, radii)):
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.0f}" fill="none" stroke="{STAR}" stroke-opacity=".3"/>')
        moons = []
        for j, p in enumerate(items):
            a = math.radians(40 + i * 75 + j * 360 / len(items))
            moons.append(f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="{moon:.1f}" fill="{MERGED if p["merged"] else STAR}" stroke="{SPACE}" stroke-width="2"/>')
        out.append(f'<g class="sp" style="--d:{70 + i * 45}s;--c:{cx}px {cy}px">{"".join(moons)}</g>')
        # Above the moons' path, so a passing moon never covers the name.
        out.append(f'<text x="{cx}" y="{cy - r - moon - 11:.0f}" text-anchor="middle" font-family="{SERIF}" font-style="italic" font-size="15" fill="{SOFT}" stroke="{SPACE}" stroke-width="4" paint-order="stroke">{esc(project(repo))}</text>')
    kx, ky = cx - radii[-1] - 112, cy - radii[-1] + 24
    out.append(f'<circle cx="{kx}" cy="{ky - 5}" r="5" fill="{MERGED}"/><text x="{kx + 13}" y="{ky}" font-family="{SERIF}" font-style="italic" font-size="14" fill="{SOFT}">merged</text>'
               f'<circle cx="{kx}" cy="{ky + 19}" r="5" fill="{STAR}"/><text x="{kx + 13}" y="{ky + 24}" font-family="{SERIF}" font-style="italic" font-size="14" fill="{SOFT}">open</text>')
    if hidden:
        out.append(f'<text x="{kx - 6}" y="{ky + 50}" font-family="{SERIF}" font-style="italic" font-size="14" fill="{SOFT}">+ {hidden} more project{"s" if hidden > 1 else ""}</text>')
    return out


def receipt():
    """A paper receipt of the work floating in space, beside an orrery of the projects."""
    x0, rw, w = 70, 590, 1280
    top = 44
    t = []

    def line(y, left, right="", size=19, weight=400, lc=INK, rc=None):
        s = f'<text x="{x0 + 36}" y="{y}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" fill="{lc}">{esc(left)}</text>'
        if right:
            s += f'<text x="{x0 + rw - 36}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="{size}" font-weight="{weight}" fill="{rc or lc}">{esc(right)}</text>'
        return s

    def rule(y):
        return f'<path d="M{x0 + 36},{y} L{x0 + rw - 36},{y}" stroke="{FAINT}" stroke-width="1.5" stroke-dasharray="2 6" stroke-linecap="round"/>'

    y = top + 56
    t.append(f'<text x="{x0 + rw / 2}" y="{y}" text-anchor="middle" font-family="{SERIF}" font-weight="700" font-size="33" fill="{INK}">Open Source Receipt</text>')
    y += 32
    t.append(f'<text x="{x0 + rw / 2}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{FAINT}">{esc(today.upper())}  ·  {esc(LOGIN.upper())}</text>')

    def section(y, title, rows):
        if not rows:
            return y
        y += 26
        t.append(rule(y))
        y += 34
        t.append(line(y, title, "", 14, 700, FAINT))
        for left, right, strong in rows:
            y += 28
            t.append(line(y, left, right, 17, 700 if strong else 400))
        return y

    shown = SM["projects"][:4]
    rows = [(name, f'{sum(p["merged"] for p in items)} merged · {sum(not p["merged"] for p in items)} open', False) for name, items in shown]
    if len(SM["projects"]) > len(shown):
        rows.append((f'+ {len(SM["projects"]) - len(shown)} more projects', "", False))
    y = section(y, "PROJECTS", rows)
    rows = [(k, str(n), False) for k, n in SM["kinds"][:6]]
    if SM["code_fixes"]:
        rows.append(("CODE FIXES WITH TESTS", f'{SM["tested"]} / {len(SM["code_fixes"])}', True))
    y = section(y, "WORK", rows)
    y = section(y, "WHERE IN THE CODE", [(area, f'{len(items)} PR{"s" if len(items) > 1 else ""}', False) for (_, area), items in SM["areas"][:6]])
    if SM["langs"]:
        y = section(y, "LANGUAGES", [(" · ".join(f"{lang} {pct}%" for lang, pct in SM["langs"][:3]), "", False)])
    y += 26
    t.append(rule(y))
    y += 38
    t.append(line(y, "PULL REQUESTS", str(len(oss)), 19, 700))
    y += 29
    t.append(line(y, "MERGED / OPEN", f"{oss_merged} / {oss_open}", 17))
    y += 27
    t.append(line(y, "LINES CHANGED", f"+{added} −{removed}", 17))
    y += 27
    t.append(line(y, "PAID IN", "code review", 17))
    y += 22
    t.append(rule(y))
    y += 20
    pos = x0 + 130
    for ch in "".join(str(p["number"]) for p in oss) or "31415926":
        n = int(ch) % 4 + 2
        if pos + n > x0 + rw - 130:
            break
        t.append(f'<rect x="{pos}" y="{y}" width="{n}" height="32" fill="{INK}"/>')
        pos += n + (int(ch) % 3) + 3
    t.append(f'<text x="{x0 + rw / 2}" y="{y + 56}" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{FAINT}">thank you for reviewing</text>')
    paper_h = y + 84 - top
    h = max(paper_h + 110, 720)
    teeth = "".join(f"L{x0 + rw - i * 20 - 10},{top + paper_h + 10} L{x0 + rw - (i + 1) * 20},{top + paper_h} " for i in range(int(rw / 20)))
    t.insert(0, f'<path d="M{x0},{top} L{x0 + rw},{top} L{x0 + rw},{top + paper_h} {teeth}Z" fill="{PAPER}"/>')
    paper = f'<g class="bob"><g transform="rotate(-1.2 {x0 + rw / 2} {top + paper_h / 2})">{"".join(t)}</g></g>'

    sx = 742

    def stat(y, big, small):
        return (f'<text x="{sx}" y="{y}" font-family="{SERIF}" font-size="52" fill="{STAR}">{esc(big)}</text>'
                f'<text x="{sx}" y="{y + 30}" font-family="{SERIF}" font-style="italic" font-size="19" fill="{SOFT}">{esc(small)}</text>')

    third = (stat(610, f"{SM['tested']} of {len(SM['code_fixes'])} fixes", "came with tests of their own") if SM["code_fixes"]
             else stat(610, f"+{added:,} −{removed:,}", "lines changed in other people's code"))
    stats = (stat(410, f"{len(oss)} pull request{'s' if len(oss) != 1 else ''}", f"across {len(oss_projects)} project{'s' if len(oss_projects) != 1 else ''}, {oss_merged} merged so far")
             + stat(510, f"{stars_combined:,} stars", "on those projects (theirs, not mine)") + third)
    label = (f"A paper receipt floating in space summing up {len(oss)} open-source pull requests by project, kind of work, "
             f"area of the code and language: {oss_merged} merged, {oss_open} open. An orrery shows them orbiting {len(oss_projects)} projects.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'{STYLE}{starfield(w, h, 23, 230)}{paper}{"".join(orrery(950, 196))}{stats}</svg>')


# ---------------------------------------------------------------- README
PLAIN = CONFIG.get("plain", {})


def impact(body):
    """The first sentence of a PR's Summary, in plain text: what it does for people."""
    text = body or ""
    m = re.search(r"^#+\s*Summary\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S)
    if m:
        text = m.group(1)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    para = next((b.strip() for b in re.split(r"\n\s*\n", text) if b.strip() and not b.strip().startswith(("#", "|", "-", "*", ">", "!", "<", "```"))), "")
    para = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", para)
    para = " ".join(re.sub(r"\*\*|__", "", para).split())
    sentence = re.split(r"(?<=[.!?])\s+(?=[A-Z])", para, maxsplit=1)[0]
    return sentence if 20 <= len(sentence) <= 240 else ""


def why(p):
    return PLAIN.get(p["url"]) or impact(p.get("body"))


def pr_line(p, with_project=False):
    """One PR as a list item, with what it does for people underneath."""
    title = p["title"].split(": ", 1)[-1]
    prefix = f"**{esc(project(p['repository']['nameWithOwner']))}** · " if with_project else ""
    line = f'- {prefix}[{esc(title)}]({p["url"]}) · <sub>{"merged" if p["merged"] else "open"}</sub>'
    value = why(p)
    return f"{line}<br>\n  {esc(value)}" if value else line


def cell(text):
    return esc(text).replace("|", "\\|")


def work_sections():
    """The summary, area table, latest merges and full list. Same size at 15 PRs or 150."""
    if not oss:
        return f"No pull requests to projects with {MIN_STARS:,}+ stars yet. The first one will show up here."
    kinds = " · ".join(f"{k} {n}" for k, n in SM["kinds"])
    lead = f"{len(oss)} pull requests to {len(SM['projects'])} projects ({kinds})."
    if SM["code_fixes"]:
        lead += f" {SM['tested']} of {len(SM['code_fixes'])} code fixes shipped with tests."
    table = "\n".join(
        f"| {cell(name)} · **{cell(area)}** | {len(items)} ({sum(p['merged'] for p in items)} merged) "
        f"| {cell(', '.join(lang for lang, _ in language_share(items)[:3]))} "
        f"| [#{items[0]['number']}]({items[0]['url']}) {cell(why(items[0]))} |"
        for (name, area), items in SM["areas"])
    merged = [p for p in oss if p["merged"]][:5]
    grouped = "\n\n".join(f"**{esc(name)}** · {len(items)}\n\n" + "\n".join(pr_line(p) for p in items) for name, items in SM["projects"])
    recent = f"### Recently merged\n\n{chr(10).join(pr_line(p, True) for p in merged)}\n\n" if merged else ""
    return f"""{lead}

### Where the work went

| Area | Pull requests | Languages | Latest change |
|---|---|---|---|
{table}

{recent}<details>
<summary>All {len(oss)} pull requests, each with what it does</summary>
<br>

{grouped}

</details>"""


def readme():
    langs = " ".join(f"`{l}`" for l in top_languages)
    built = "\n".join(
        f'- **[{esc(b.get("title", b["repo"]))}]({repo_by_name[b["repo"]]["url"]})** · {esc(b.get("line", ""))}'
        for b in CONFIG.get("built", []) if b.get("repo") in repo_by_name)
    team_block = ""
    if team and CONFIG.get("show_smaller_projects", True):
        rows = "\n".join(f'| {esc(p["repository"]["nameWithOwner"])} | [{esc(p["title"])}]({p["url"]}) | {"Merged" if p["merged"] else p["state"].title()} |' for p in team)
        team_block = f"""
<details>
<summary>Smaller projects ({len(team)} PRs)</summary>
<br>

| Repository | Pull request | Status |
|---|---|---|
{rows}

</details>
"""
    extra = (ROOT / "extra.md").read_text(encoding="utf8").strip() if (ROOT / "extra.md").exists() else ""
    intro = CONFIG.get("intro", "")
    return f"""<img src="assets/cover.svg" alt="{esc(NAME)}, over a slow star-trail sky, with a constellation of real pull requests." width="100%">

{intro + chr(10) + chr(10) if intro else ""}{langs} &nbsp;·&nbsp; {user["repositories"]["totalCount"]} public repos &nbsp;·&nbsp; on GitHub since {since}

## Receipts

<img src="assets/receipt.svg" alt="Paper receipt floating in space: {len(oss)} pull requests, {oss_merged} merged, {oss_open} open, plus {added} and minus {removed} lines." width="100%">

{work_sections()}
{team_block}{chr(10) + "## Built" + chr(10) + chr(10) + built + chr(10) if built else ""}{chr(10) + extra + chr(10) if extra else ""}
<sub>Numbers from the GitHub API, last updated {esc(today)}. Made with [orbit-profile](https://github.com/ityashag/orbit-profile).</sub>
"""


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = pathlib.Path(os.environ.get("ORBIT_OUT", ROOT))
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "cover.svg").write_text(cover(), encoding="utf8")
    (out / "assets" / "receipt.svg").write_text(receipt(), encoding="utf8")
    (out / "README.md").write_text(readme(), encoding="utf8")
    print(json.dumps({"login": LOGIN, "prs": len(prs), "oss": len(oss), "merged": oss_merged, "open": oss_open,
                      "projects": len(oss_projects), "stars": stars_combined, "smaller": len(team)}))
