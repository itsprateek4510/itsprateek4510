"""Build self-contained GitHub profile SVGs with live, authenticated stats."""

import argparse
from calendar import monthrange
from datetime import date, datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.photo_to_ascii import photo_to_ascii


ROOT = Path(__file__).resolve().parents[1]
USER_QUERY = """query($login: String!) {
  user(login: $login) { id followers { totalCount } }
}"""
REPOS_QUERY = """query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false) {
      nodes { nameWithOwner stargazerCount }
      pageInfo { hasNextPage endCursor }
    }
  }
}"""
HISTORY_QUERY = """query($owner: String!, $name: String!, $author: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, after: $cursor, author: {id: $author}) {
        totalCount nodes { additions deletions }
        pageInfo { hasNextPage endCursor }
      }
    } } }
  }
}"""
THEMES = {
    "dark": dict(bg="#0d1117", chrome="#161b22", border="#30363d", key="#58a6ff",
                 value="#f0f6fc", muted="#8b949e", art="#a5c9ff", add="#3fb950", delete="#f85149"),
    "light": dict(bg="#ffffff", chrome="#f6f8fa", border="#d0d7de", key="#0969da",
                  value="#1f2328", muted="#656d76", art="#344d6c", add="#1a7f37", delete="#cf222e"),
}


def github_request(query, variables, token):
    request = Request("https://api.github.com/graphql",
                      data=json.dumps({"query": query, "variables": variables}).encode(),
                      headers={"Authorization": f"Bearer {token}",
                               "Accept": "application/vnd.github+json",
                               "Content-Type": "application/json",
                               "User-Agent": "github-profile-neofetch"})
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code}; check token access/rate limits.") from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach GitHub: {error.reason}") from error
    if payload.get("errors"):
        raise RuntimeError("GitHub GraphQL: " + "; ".join(e["message"] for e in payload["errors"]))
    return payload["data"]


def fetch_stats(username, token):
    user = github_request(USER_QUERY, {"login": username}, token)["user"]
    if user is None:
        raise RuntimeError(f"GitHub user {username!r} not found.")
    repositories, cursor = [], None
    while True:
        page = github_request(REPOS_QUERY, {"login": username, "cursor": cursor}, token)
        page = page["user"]["repositories"]
        repositories.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    stats = dict(repos=len(repositories), stars=sum(r["stargazerCount"] for r in repositories),
                 followers=user["followers"]["totalCount"], commits=0, additions=0, deletions=0)
    for repository in repositories:
        owner, name = repository["nameWithOwner"].split("/", 1)
        cursor = None
        while True:
            data = github_request(HISTORY_QUERY, {"owner": owner, "name": name,
                                  "author": user["id"], "cursor": cursor}, token)
            branch = data["repository"]["defaultBranchRef"]
            if branch is None:
                break
            page = branch["target"]["history"]
            if cursor is None:
                stats["commits"] += page["totalCount"]
            for commit in page["nodes"]:
                stats["additions"] += commit["additions"]
                stats["deletions"] += commit["deletions"]
            if not page["pageInfo"]["hasNextPage"]:
                break
            cursor = page["pageInfo"]["endCursor"]
    return stats


def calculate_uptime(birthday, today):
    """Count full calendar months, clamping anniversaries to month end."""
    born = datetime.strptime(birthday, "%d-%m-%Y").date()
    if born > today:
        raise ValueError("Birth date cannot be in the future.")
    months = (today.year - born.year) * 12 + today.month - born.month
    for elapsed in (months, months - 1):
        year, month = divmod(born.year * 12 + born.month - 1 + elapsed, 12)
        anchor = date(year, month + 1, min(born.day, monthrange(year, month + 1)[1]))
        if anchor <= today:
            years, remaining_months = divmod(elapsed, 12)
            return f"{years} years, {remaining_months} months, {(today - anchor).days} days"


def render_svg(config, portrait, stats, theme, today, uptime=None):
    colors = THEMES[theme]
    rows = [("header", f'{config["username"]}@github'), ("muted", "─" * 34),
            ("Name", config["name"]), ("Kernel", config["role"])]
    if uptime:
        rows.append(("Uptime", uptime))
    rows.extend(config["info"])
    rows.extend([("blank", ""), ("section", "— Projects")])
    rows.extend(("project", project) for project in config["projects"])
    rows.extend([("blank", ""), ("section", "— Contact"),
                 ("Email", config["email"]), ("LinkedIn", config["linkedin"]),
                 ("blank", ""), ("section", "— GitHub Stats")])
    for label, key in (("Repos", "repos"), ("Commits", "commits"),
                       ("Stars", "stars"), ("Followers", "followers")):
        rows.append((label, f"{stats[key]:,}" if stats is not None else "not synced"))
    rows.append(("Lines of Code", "" if stats is not None else "not synced"))
    width = max(1120, int(552 + max(26 + len(value) for _, value in rows) * 8.1 + 32))
    height = max(748, 126 + (len(rows) - 1) * 23 + 72)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
           f'<title id="title">{escape(config["name"])} — neofetch</title>',
           '<desc id="description">ASCII head-and-shoulders portrait beside a developer profile. '
           'Stats cover owned, non-fork repositories and authored default-branch history. '
           'Lines of Code means cumulative additions and deletions, not current code size.</desc>',
           f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14" '
           f'fill="{colors["bg"]}" stroke="{colors["border"]}"/>',
           f'<path d="M15 1 H{width - 15} Q{width - 1} 1 {width - 1} 15 V48 H1 V15 Q1 1 15 1" '
           f'fill="{colors["chrome"]}"/>',
           f'<path d="M1 48 H{width - 1}" stroke="{colors["border"]}"/>',
           '<circle cx="25" cy="25" r="5" fill="#ff5f57"/>',
           '<circle cx="44" cy="25" r="5" fill="#febc2e"/>',
           '<circle cx="63" cy="25" r="5" fill="#28c840"/>',
           '<g font-family="Consolas, \'Fira Code\', \'Liberation Mono\', monospace" '
           f'font-size="13" fill="{colors["value"]}">',
           f'<text x="{width / 2:g}" y="30" text-anchor="middle" fill="{colors["muted"]}">'
           f'{escape(config["username"])} — ~/github</text>',
           f'<text x="32" y="84"><tspan fill="{colors["add"]}">$ </tspan>'
           'neofetch --ascii ./myphoto.jpg</text>',
           f'<path d="M526 110 V{height - 65}" stroke="{colors["border"]}"/>',
           f'<text id="portrait" x="32" y="126" xml:space="preserve" font-size="14" fill="{colors["art"]}">']
    for index, line in enumerate(portrait):
        svg[-1] += (f'<tspan x="32" y="{126 + index * 16.8:.1f}" textLength="462" '
                    f'lengthAdjust="spacingAndGlyphs">{escape(line)}</tspan>')
    svg[-1] += '</text>'
    svg.extend([f'<text x="263" y="658" text-anchor="middle" '
                f'fill="{colors["key"]}" font-weight="bold">{escape(config["name"])}</text>',
                f'<text x="263" y="682" text-anchor="middle" fill="{colors["muted"]}">'
                'I build the logic behind the interface.</text>'])
    for index, (label, value) in enumerate(rows):
        y = 126 + index * 23
        if label == "blank":
            continue
        if label in ("header", "section", "muted", "project"):
            color = colors["key"] if label in ("header", "section") else colors["muted"]
            svg.append(f'<text x="552" y="{y}" fill="{color}">{escape(value)}</text>')
            continue
        prefix = f'{label}: ' + '.' * max(2, 23 - len(label)) + ' '
        content = escape(value)
        if label == "Lines of Code" and stats is not None:
            content = (f'<tspan fill="{colors["add"]}">+{stats["additions"]:,}</tspan>'
                       f'<tspan fill="{colors["muted"]}"> / </tspan>'
                       f'<tspan fill="{colors["delete"]}">-{stats["deletions"]:,}</tspan>')
        svg.append(f'<text x="552" y="{y}" xml:space="preserve">'
                   f'<tspan fill="{colors["key"]}">{escape(label)}:</tspan>'
                   f'<tspan fill="{colors["muted"]}">{escape(prefix[len(label) + 1:])}</tspan>'
                   f'<tspan>{content}</tspan></text>')
    for index, color in enumerate((colors["border"], colors["delete"], colors["add"],
                                   "#d29922", colors["key"], "#bc8cff", "#39c5cf", colors["value"])):
        svg.append(f'<rect x="{151 + index * 28}" y="706" width="28" height="12" fill="{color}"/>')
    status = f"Updated {today.isoformat()} UTC" if stats is not None else "PREVIEW — stats not synced"
    svg.extend([f'<text x="32" y="{height - 22}" fill="{colors["muted"]}" font-size="11">'
                f'{status} · owned non-fork repos · authored default-branch history</text>', '</g>', '</svg>'])
    return "\n".join(svg) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets")
    parser.add_argument("--preview", action="store_true", help="Offline layout; stats say 'not synced'.")
    args = parser.parse_args(argv)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not args.preview and not token:
        raise SystemExit("Set GH_TOKEN (or GITHUB_TOKEN) to a GitHub token, or use --preview.")
    config = json.loads((ROOT / "profile.json").read_text())
    today = datetime.now(timezone.utc).date()
    birthday = os.environ.get("PROFILE_BIRTH_DATE")
    uptime = calculate_uptime(birthday, today) if birthday else None
    portrait = photo_to_ascii(ROOT / config["photo"], crop=config["crop"])
    stats = None if args.preview else fetch_stats(config["username"], token)
    # Finish API requests and rendering before touching the checked-in assets.
    images = {theme: render_svg(config, portrait, stats, theme, today, uptime) for theme in THEMES}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "portrait.txt").write_text("\n".join(portrait) + "\n", encoding="utf-8")
    for theme, svg in images.items():
        (args.output_dir / f"{theme}.svg").write_text(svg, encoding="utf-8")
    print(f"Generated dark.svg, light.svg, and portrait.txt in {args.output_dir}")


if __name__ == "__main__":
    main()
