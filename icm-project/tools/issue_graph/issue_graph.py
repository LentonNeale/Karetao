#!/usr/bin/env python3
"""issue_graph: open issues, their native dependencies, and the board Status and order they imply.

Reads GitHub through the `gh` CLI (no token handling here). Writes nothing unless --apply or
--set-status is given. See issue_graph.md for the rules.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

REPO = "LentonNeale/Karetao"
PROJECT_OWNER = "LentonNeale"
PROJECT_NUMBER = 4
COMPUTED = ("Backlog", "Ready", "Blocked")          # statuses this tool owns
HUMAN = ("In Progress", "Verification", "Done")     # statuses it never overwrites


def gh(*args: str, input_json: dict | None = None) -> dict | list:
    cmd = ["gh", *args]
    data = json.dumps(input_json) if input_json is not None else None
    res = subprocess.run(cmd, input=data, capture_output=True, text=True)
    if res.returncode != 0:
        err = res.stderr.strip()
        if "read:project" in err or "project" in err and "scope" in err:
            sys.exit("gh lacks the project scope. Run in a terminal:\n"
                     "  gh auth refresh -h github.com -s read:project,project\n"
                     "and authorise as AIKaretao (the account gh is logged in as). "
                     "Lenton must also have added AIKaretao to the board under Manage access.")
        sys.exit(f"gh failed: {' '.join(cmd)}\n{err}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def graphql(query: str, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        args += ["-F" if isinstance(v, (int, float)) else "-f", f"{k}={v}"]
    out = gh(*args)
    if "errors" in out:
        sys.exit("GraphQL errors: " + json.dumps(out["errors"], indent=1))
    return out["data"]


# ----------------------------------------------------------------------------- issues and edges

def open_issues(repo: str) -> list[dict]:
    items = gh("api", f"repos/{repo}/issues?state=open&per_page=100")
    issues = []
    for it in items:
        if "pull_request" in it:
            continue
        issues.append({
            "number": it["number"],
            "title": it["title"],
            "milestone": (it.get("milestone") or {}).get("title"),
            "milestone_number": (it.get("milestone") or {}).get("number"),
            "node_id": it["node_id"],
            "blocking": it.get("issue_dependencies_summary", {}).get("blocking", 0),
            "blocked_by_count": it.get("issue_dependencies_summary", {}).get("blocked_by", 0),
            "blocked_by": [],
        })
    for iss in issues:
        if iss["blocked_by_count"]:
            deps = gh("api", f"repos/{repo}/issues/{iss['number']}/dependencies/blocked_by")
            iss["blocked_by"] = sorted(d["number"] for d in deps if d.get("state") == "open")
    return issues


def stage_key(milestone: str | None) -> tuple:
    """Stage N milestones in order; cross-stage (no milestone) after them."""
    if milestone and milestone.startswith("Stage "):
        try:
            return (0, int(milestone.split()[1]))
        except ValueError:
            pass
    return (1, 0) if milestone is None else (0, 99)


def compute(issues: list[dict]) -> list[dict]:
    stages = sorted({stage_key(i["milestone"]) for i in issues if i["milestone"]})
    current = stages[0] if stages else None
    for i in issues:
        if i["blocked_by"]:
            i["computed"] = "Blocked"
        elif i["milestone"] is None or stage_key(i["milestone"]) == current:
            i["computed"] = "Ready"
        else:
            i["computed"] = "Backlog"
    # Order: stage, then the issue that unblocks the most others first, then number.
    issues.sort(key=lambda i: (stage_key(i["milestone"]), -i["blocking"], i["number"]))
    return issues


def print_plan(issues: list[dict]) -> None:
    last = object()
    for i in issues:
        if i["milestone"] != last:
            print(f"\n{i['milestone'] or 'No milestone (cross-stage)'}")
            last = i["milestone"]
        blockers = ", ".join(f"#{n}" for n in i["blocked_by"]) or "-"
        print(f"  #{i['number']:<3} {i['computed']:<8} blocks {i['blocking']:<2} blocked by {blockers:<14} {i['title']}")
    ready = [i for i in issues if i["computed"] == "Ready"]
    print(f"\nReady now: {', '.join(f'#{i['number']}' for i in ready) or 'nothing'}")


# ----------------------------------------------------------------------------- board

PROJECT_QUERY = """
query($owner:String!, $number:Int!) {
  user(login:$owner) { projectV2(number:$number) {
    id
    field(name:"Status") { ... on ProjectV2SingleSelectField { id options { id name } } }
    blocking: field(name:"Blocking") { ... on ProjectV2Field { id } }
    items(first:100) { nodes { id content { ... on Issue { number } } fieldValues(first:20) {
      nodes { ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2Field { name } } } } } } }
  } }
}"""


def load_board():
    data = graphql(PROJECT_QUERY, owner=PROJECT_OWNER, number=PROJECT_NUMBER)
    proj = data["user"]["projectV2"]
    if proj is None:
        sys.exit(f"Project {PROJECT_NUMBER} not visible to this token (closed, or AIKaretao not a collaborator).")
    options = {o["name"]: o["id"] for o in proj["field"]["options"]}
    missing = [s for s in COMPUTED + HUMAN if s not in options]
    if missing:
        sys.exit(f"Board Status field lacks options {missing}; add them in the board settings (ISSUE_CONTRACT.md).")
    items = {}
    for node in proj["items"]["nodes"]:
        num = (node.get("content") or {}).get("number")
        if num is None:
            continue
        status = next((fv["name"] for fv in node["fieldValues"]["nodes"]
                       if fv and fv.get("field", {}).get("name") == "Status"), None)
        blocking = next((fv["number"] for fv in node["fieldValues"]["nodes"]
                         if fv and fv.get("field", {}).get("name") == "Blocking"), None)
        items[num] = {"item_id": node["id"], "status": status, "blocking": blocking}
    blocking_field = (proj.get("blocking") or {}).get("id")
    return proj["id"], proj["field"]["id"], options, items, blocking_field


def apply(issues: list[dict], dry: bool) -> None:
    project_id, field_id, options, items, blocking_field = load_board()
    changes = []
    for i in issues:
        if i["number"] not in items:
            changes.append(("add", i["number"], None))
    for i in issues:
        cur = items.get(i["number"], {}).get("status")
        if cur in HUMAN:
            continue
        if cur != i["computed"]:
            changes.append(("status", i["number"], i["computed"]))
    if blocking_field:
        for i in issues:
            if items.get(i["number"], {}).get("blocking") != i["blocking"]:
                changes.append(("blocking", i["number"], i["blocking"]))
    else:
        print("(no 'Blocking' number field on the board; counts not written)")
    changes.append(("order", [i["number"] for i in issues], None))
    for kind, a, b in changes:
        if kind == "add":
            print(f"add #{a} to board")
        elif kind == "status":
            print(f"#{a}: Status -> {b}")
        elif kind == "blocking":
            print(f"#{a}: Blocking -> {b}")
        else:
            print("order: " + " ".join(f"#{n}" for n in a))
    if dry:
        print("\n(dry run: nothing written; pass --apply to write)")
        return
    # 1. add missing items
    for kind, num, _ in changes:
        if kind != "add":
            continue
        node = next(i["node_id"] for i in issues if i["number"] == num)
        res = graphql('mutation($p:ID!,$c:ID!){ addProjectV2ItemById(input:{projectId:$p, contentId:$c}){ item { id } } }',
                      p=project_id, c=node)
        items[num] = {"item_id": res["addProjectV2ItemById"]["item"]["id"], "status": None}
    # 2. statuses
    for kind, num, status in changes:
        if kind != "status":
            continue
        graphql('mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item { id } } }',
                p=project_id, i=items[num]["item_id"], f=field_id, o=options[status])
    # 2b. blocking counts
    for kind, num, count in changes:
        if kind != "blocking":
            continue
        graphql('mutation($p:ID!,$i:ID!,$f:ID!,$n:Float!){ updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:{number:$n}}){ projectV2Item { id } } }',
                p=project_id, i=items[num]["item_id"], f=blocking_field, n=int(count))
    # 3. order: walk the list, placing each item after the previous one
    prev = None
    for num in [i["number"] for i in issues]:
        item = items[num]["item_id"]
        if prev is None:
            graphql('mutation($p:ID!,$i:ID!){ updateProjectV2ItemPosition(input:{projectId:$p, itemId:$i}){ items(first:1){ totalCount } } }',
                    p=project_id, i=item)
        else:
            graphql('mutation($p:ID!,$i:ID!,$a:ID!){ updateProjectV2ItemPosition(input:{projectId:$p, itemId:$i, afterId:$a}){ items(first:1){ totalCount } } }',
                    p=project_id, i=item, a=prev)
        prev = item
    print("board updated")


def set_status(number: int, status: str) -> None:
    if status not in COMPUTED + HUMAN:
        sys.exit(f"unknown status {status!r}; one of {COMPUTED + HUMAN}")
    project_id, field_id, options, items, _ = load_board()
    if number not in items:
        sys.exit(f"#{number} is not on the board; run --apply first")
    graphql('mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{projectId:$p, itemId:$i, fieldId:$f, value:{singleSelectOptionId:$o}}){ projectV2Item { id } } }',
            p=project_id, i=items[number]["item_id"], f=field_id, o=options[status])
    print(f"#{number}: Status -> {status}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--json", action="store_true", help="print the computed graph as JSON")
    ap.add_argument("--board", action="store_true", help="also show the board changes implied (dry run)")
    ap.add_argument("--apply", action="store_true", help="write Status and order to the board")
    ap.add_argument("--set-status", nargs=2, metavar=("NUMBER", "STATUS"),
                    help="set one issue's board Status by hand (In Progress, Verification, ...)")
    args = ap.parse_args()
    if args.set_status:
        set_status(int(args.set_status[0]), args.set_status[1])
        return
    issues = compute(open_issues(args.repo))
    if args.json:
        print(json.dumps(issues, indent=1))
    else:
        print_plan(issues)
    if args.board or args.apply:
        print()
        apply(issues, dry=not args.apply)


if __name__ == "__main__":
    main()
