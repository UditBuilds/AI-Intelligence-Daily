"""Open-issue lookup for the #prism-glamshelf slot.

Pulls open issues from the founder's two live repos and picks the one most
worth acting on today. Returns None when nothing usable is open, which is the
signal for the suggester to fall back to a context-grounded idea instead.
"""

import logging

import requests

from config import (
    GITHUB_API,
    GITHUB_ISSUE_REPOS,
    GITHUB_TOKEN,
    GITHUB_TIMEOUT,
    MIN_ISSUE_TITLE_LEN,
)

logger = logging.getLogger(__name__)

# Titles that carry no actionable signal on their own.
_VAGUE_TITLES = {
    "bug", "bugs", "todo", "todos", "fix", "fixes", "issue", "issues",
    "improvement", "improvements", "enhancement", "enhancements", "idea",
    "ideas", "question", "test", "testing", "wip", "misc", "cleanup",
    "refactor", "update", "updates", "notes",
}


def _headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AIIntelligenceDaily/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _is_usable(issue) -> bool:
    """Drop pull requests, stub titles, and single-generic-word titles."""
    # The issues endpoint returns PRs too; they carry a pull_request key.
    if issue.get("pull_request"):
        return False
    title = (issue.get("title") or "").strip()
    if len(title) < MIN_ISSUE_TITLE_LEN:
        return False
    if title.strip(" .!?:-").lower() in _VAGUE_TITLES:
        return False
    return True


def _fetch_repo_issues(repo: str):
    url = f"{GITHUB_API}/repos/{repo}/issues"
    params = {"state": "open", "sort": "created", "direction": "asc", "per_page": 50}
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=GITHUB_TIMEOUT)
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        logger.warning("Could not read issues from %s: %s", repo, e)
        return []

    issues = []
    for issue in raw:
        if not _is_usable(issue):
            continue
        issues.append({
            "repo": repo,
            "number": issue.get("number"),
            "title": (issue.get("title") or "").strip(),
            "body": (issue.get("body") or "").strip()[:1200],
            "comments": issue.get("comments", 0) or 0,
            "created_at": issue.get("created_at") or "",
            "labels": [l.get("name", "") for l in issue.get("labels", []) if isinstance(l, dict)],
            "url": issue.get("html_url") or "",
        })
    logger.info("%s: %d usable open issues.", repo, len(issues))
    return issues


def pick_issue(exclude_urls=()):
    """Return the highest-priority open issue across both repos, or None.

    Priority is most-commented first, oldest breaking the tie — a busy issue is
    the clearest demand signal, and among equally quiet ones the one that has
    been waiting longest wins. ``exclude_urls`` skips issues already used as a
    source in a recent suggestion so the slot does not stall on one ticket.
    """
    excluded = {u for u in exclude_urls if u}
    pool = []
    for repo in GITHUB_ISSUE_REPOS:
        pool.extend(_fetch_repo_issues(repo))

    fresh = [i for i in pool if i["url"] not in excluded]
    if not fresh:
        logger.info(
            "No usable open issue (%d found, %d already used recently); falling back.",
            len(pool), len(pool) - len(fresh),
        )
        return None

    fresh.sort(key=lambda i: (-i["comments"], i["created_at"]))
    best = fresh[0]
    logger.info(
        "Slot 1 grounded in %s#%s (%d comments): %s",
        best["repo"], best["number"], best["comments"], best["title"],
    )
    return best
