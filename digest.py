"""
Free weekly digest of new open-source AI tools that work with Claude, posted to Discord.

No AI and no paid APIs: it searches GitHub for recently created repos about
Claude, Claude Code, Anthropic and MCP, ranks them by stars, skips anything
already posted, and sends the top picks to a Discord webhook.

Env vars:
  DISCORD_WEBHOOK_URL  - required (unless DRY_RUN is set)
  GITHUB_TOKEN         - optional locally, provided automatically in GitHub Actions
  LOOKBACK_DAYS        - optional, how far back "new" goes (default 30)
  MIN_STARS            - optional, minimum stars to be featured (default 20)
  DRY_RUN              - optional, if set prints the Discord message instead of posting
"""

import datetime
import json
import os
import pathlib
import re

import requests

LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "30"))
MIN_STARS = int(os.environ.get("MIN_STARS", "20"))
MAX_TOOLS = 8            # Discord allows 10 embeds per message
HISTORY_LIMIT = 500      # how many past repos to remember so nothing repeats
HISTORY_FILE = pathlib.Path(__file__).with_name("seen_tools.json")

# GitHub searches to run. Results are merged, de-duplicated and ranked by stars.
SEARCHES = [
    "topic:claude-code",
    "topic:claude",
    "topic:anthropic",
    "topic:mcp-server",
    "topic:claude-skills",
    "claude in:name,description",
    '"model context protocol" in:name,description',
]

# A repo must mention at least one of these to count as working with Claude.
RELEVANT = re.compile(r"claude|anthropic|\bmcp\b|model context protocol", re.IGNORECASE)


def load_history() -> list[str]:
    try:
        return json.loads(HISTORY_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history: list[str]) -> None:
    HISTORY_FILE.write_text(json.dumps(history[-HISTORY_LIMIT:], indent=2) + "\n")


def github_search(query: str, since: str) -> list[dict] | None:
    """Return matching repos, or None if the search failed."""
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    params = {
        "q": f"{query} created:>={since} stars:>={MIN_STARS} fork:false archived:false",
        "sort": "stars",
        "order": "desc",
        "per_page": 50,
    }
    resp = requests.get("https://api.github.com/search/repositories",
                        params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Search failed ({resp.status_code}) for {query!r}: {resp.text[:200]}")
        return None
    return resp.json().get("items", [])


def repo_text(repo: dict) -> str:
    return " ".join([repo.get("name") or "", repo.get("description") or "",
                     " ".join(repo.get("topics") or [])]).lower()


def claude_angle(repo: dict) -> str:
    text, topics = repo_text(repo), set(repo.get("topics") or [])
    if "claude-code" in topics or "claude code" in text or "claude-code" in text:
        return "Claude Code tool, plugin or skill"
    if re.search(r"\bmcp\b|model context protocol", text):
        return "MCP server: connect it to Claude Desktop or Claude Code"
    return "Built for Claude or the Claude API"


def licence(repo: dict) -> str:
    spdx = (repo.get("license") or {}).get("spdx_id")
    if spdx and spdx != "NOASSERTION":
        return f"Open source ({spdx})"
    return "Public repo, no licence listed"


def find_tools(seen: set[str]) -> list[dict]:
    since = (datetime.date.today() - datetime.timedelta(days=LOOKBACK_DAYS)).isoformat()
    found: dict[str, dict] = {}
    results = [github_search(query, since) for query in SEARCHES]
    if all(r is None for r in results):
        raise SystemExit("Every GitHub search failed, so nothing was posted. See the errors above.")
    for repos in results:
        for repo in repos or []:
            name = repo["full_name"]
            if (name.lower() in seen or name in found or not repo.get("description")
                    or not RELEVANT.search(repo_text(repo))):
                continue
            found[name] = repo
    return sorted(found.values(), key=lambda r: r["stargazers_count"], reverse=True)[:MAX_TOOLS]


def clip(text, limit: int) -> str:
    text = str(text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def build_payload(repos: list[dict]) -> dict:
    week = datetime.date.today().strftime("%d %b %Y")
    header = f"**Free AI tools for Claude: week of {week}**\n"
    if not repos:
        return {"username": "AI Tools Weekly",
                "content": header + "Quiet week: nothing new passed the filters. See you next Monday!"}

    embeds = [{
        "title": clip(r["full_name"], 256),
        "url": r["html_url"],
        "description": clip(r["description"], 1000),
        "color": 0xD97757,
        "fields": [
            {"name": "Works with Claude", "value": claude_angle(r)},
            {"name": "Stars", "value": f"⭐ {r['stargazers_count']:,}", "inline": True},
            {"name": "Licence", "value": licence(r), "inline": True},
            {"name": "Language", "value": r.get("language") or "n/a", "inline": True},
        ],
    } for r in repos]

    return {
        "username": "AI Tools Weekly",
        "content": header + f"Top new GitHub projects from the last {LOOKBACK_DAYS} days, ranked by stars. "
                            "Check a tool's code and permissions before connecting it to Claude.",
        "embeds": embeds,
    }


def post(payload: dict) -> None:
    if os.environ.get("DRY_RUN"):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    resp = requests.post(os.environ["DISCORD_WEBHOOK_URL"], json=payload, timeout=30)
    resp.raise_for_status()


def main() -> None:
    history = load_history()
    repos = find_tools({h.lower() for h in history})
    post(build_payload(repos))
    if not os.environ.get("DRY_RUN"):
        history.extend(r["full_name"] for r in repos)
        save_history(history)
    print(f"Featured {len(repos)} tools.")


if __name__ == "__main__":
    main()
