"""
Views for the ICM GUI server.
"""

import html
import urllib.parse
from pathlib import Path
from urllib.parse import urlencode, parse_qs

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from icmlib import check_inside_outputs, read_header, read_reviews, list_artifacts, checkpoint_of, open_questions, task_tier
from helper import get_store
import checkpoint_policy


def shared_layout(title, body, role, viewer_identity, active_tab):
    """Render shared layout with tabs by role."""
    tabs_html = ""

    if role == "helper":
        tabs = [
            ("/helper", "Helper"),
            ("/pipeline", "Pipeline"),
        ]
    else:  # user or agent
        tabs = [
            ("/", "Queue"),
            ("/pipeline", "Pipeline"),
            ("/helper", "Helper"),
            ("/audit", "Audit"),
        ]

    for path, label in tabs:
        active_class = "active" if active_tab == path else ""
        tabs_html += f'<a href="{path}" class="tab {active_class}">{label}</a>'

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <h1>ICM Prototype</h1>
        <div class="identity">Viewing as {html.escape(viewer_identity)}</div>
    </header>
    <nav class="tabs">
        {tabs_html}
    </nav>
    <main>
        {body}
    </main>
</body>
</html>"""


def render_queue(status_data, root, role):
    """Render the queue page for users."""
    if role == "helper":
        return None

    # Filter for user-awaiting items
    user_awaiting = []
    for task in status_data:
        for artifact in task["artifacts"]:
            if artifact["awaiting"] == "user":
                user_awaiting.append({
                    "task": task["task"],
                    "tier": task["tier"],
                    "artifact": artifact,
                })

    # Sort: blocking first, then by mtime (oldest first)
    user_awaiting.sort(
        key=lambda x: (not x["artifact"]["blocking"], float(x["artifact"]["mtime"]))
    )

    # Group by blocking
    blocking_items = [item for item in user_awaiting if item["artifact"]["blocking"]]
    non_blocking_items = [item for item in user_awaiting if not item["artifact"]["blocking"]]

    html_parts = []
    html_parts.append('<div class="queue-list">')

    for items, is_blocking in [(blocking_items, True), (non_blocking_items, False)]:
        for item in items:
            art = item["artifact"]
            badge_class = "badge-blocking" if is_blocking else "badge-non-blocking"
            badge_text = "Blocking" if is_blocking else "Non-blocking"

            artifact_link = f'/artifact?path={urlencode({"path": art["path"]})}'.split("=", 1)[0] + "=" + art["path"]
            tier_str = item["tier"] if item["tier"] else "—"

            html_parts.append(f"""
    <div class="queue-item">
        <div class="queue-header">
            <span class="badge {badge_class}">{badge_text}</span>
            <span class="task-name">{html.escape(item["task"])}</span>
            <span class="tier">Tier {html.escape(tier_str)}</span>
        </div>
        <div class="artifact-info">
            <a href="{artifact_link}">{html.escape(art["path"])}</a>
            <span class="reason">{html.escape(art["reason"])}</span>
        </div>
    </div>
""")

    html_parts.append('</div>')

    body = '\n'.join(html_parts) if user_awaiting else '<p>No items awaiting user approval.</p>'
    return body


def render_pipeline(status_data, root):
    """Render the pipeline page (tasks × stages)."""
    stages = ["01-intake", "02-issue-spec", "03-design", "04-implement", "05-verify", "06-close-out"]

    # Build a map of task × stage → artifact info
    task_stage_map = {}
    for task in status_data:
        task_name = task["task"]
        if task_name not in task_stage_map:
            task_stage_map[task_name] = {}

        for artifact in task["artifacts"]:
            stage = artifact["stage"]
            task_stage_map[task_name][stage] = artifact

    # Start the table
    html_parts = ['<table class="pipeline-table">']
    html_parts.append('<thead><tr><th>Task</th><th>Tier</th>')
    for stage in stages:
        # Extract just the stage number
        stage_num = stage.split("-")[0]
        html_parts.append(f'<th>{html.escape(stage_num)}</th>')
    html_parts.append('</tr></thead>')

    html_parts.append('<tbody>')
    for task in status_data:
        task_name = task["task"]
        tier = task["tier"] if task["tier"] else "—"
        can_proceed = "✓ proceed" if task["can_proceed"] else "✗ blocked"

        evidence_link = "/evidence?task=" + urllib.parse.quote(task_name)
        html_parts.append(f'<tr><td class="task-name">{html.escape(task_name)} '
                          f'<a href="{html.escape(evidence_link)}">evidence</a></td>')
        html_parts.append(f'<td>{html.escape(tier)}</td>')

        for stage in stages:
            artifact = task_stage_map.get(task_name, {}).get(stage)
            if artifact:
                artifact_link = "/artifact?path=" + urllib.parse.quote(artifact["path"])
                html_parts.append(f'<td><a href="{artifact_link}">{html.escape(artifact["checkpoint"])}</a></td>')
            else:
                html_parts.append('<td>—</td>')

        html_parts.append('</tr>')

    html_parts.append('</tbody>')
    html_parts.append('</table>')

    body = '\n'.join(html_parts)
    return body


def render_action_forms(artifact_path, header, role, viewer_identity):
    """Render action forms for the artifact page based on role and permissions."""
    if not header or role == "helper":
        return ""

    # Get checkpoint and task info
    cp = checkpoint_of(artifact_path)
    task = header.get("task", "")
    status = header.get("status", "")
    author = header.get("author", "")
    approver = header.get("approver", "")

    if not cp or not task:
        return ""

    forms_html = '<div class="action-forms">\n'

    # Show disabled approve button with reason if not allowed
    # artifact_path is ROOT/stages/NN-name/output/<file>, so ROOT is three levels up
    tier = task_tier(Path(artifact_path).resolve().parents[3], task)
    open_q = open_questions(artifact_path)
    allowed, reason = checkpoint_policy.may_approve(cp, tier, author, viewer_identity)

    if allowed and open_q == 0:
        forms_html += f'''    <form method="post" action="/action" style="display:inline;">
        <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
        <input type="hidden" name="action" value="approve">
        <button type="submit">Approve</button>
    </form>\n'''
    else:
        why = f"{open_q} open question(s) must be answered first" if allowed else reason
        forms_html += f'''    <button disabled title="{html.escape(why)}">Approve</button> <small>{html.escape(why)}</small>\n'''

    # Request changes (users only)
    if role == "user":
        forms_html += f'''    <form method="post" action="/action" style="display:inline;">
        <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
        <input type="hidden" name="action" value="request-changes">
        <input type="text" name="text" placeholder="Change request" required>
        <button type="submit">Request Changes</button>
    </form>\n'''

    # Comment (users and agents)
    if role in ("user", "agent"):
        forms_html += f'''    <form method="post" action="/action" style="display:inline;">
        <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
        <input type="hidden" name="action" value="comment">
        <input type="text" name="text" placeholder="Comment" required>
        <button type="submit">Comment</button>
    </form>\n'''

    # Ask question (users, brief and spec only)
    if role == "user" and cp in ("C1", "C2"):
        forms_html += f'''    <form method="post" action="/action" style="display:inline;">
        <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
        <input type="hidden" name="action" value="ask">
        <input type="text" name="text" placeholder="Question" required>
        <button type="submit">Ask</button>
    </form>\n'''

    # Set tier (users only, brief only)
    if role == "user" and cp == "C1":
        tier_suggested = header.get("tier_suggested", "")
        forms_html += f'''    <div class="tier-buttons">
        <span>Set Tier:</span>\n'''
        for tier_val in ["T1", "T2", "T3", "T4"]:
            checked = "checked" if tier_val == tier_suggested else ""
            forms_html += f'''        <form method="post" action="/action" style="display:inline;">
            <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
            <input type="hidden" name="action" value="set-tier">
            <input type="hidden" name="tier" value="{tier_val}">
            <button type="submit">{tier_val}</button>
        </form>\n'''
        forms_html += '''    </div>\n'''

    # Reopen (users only, when approver is an agent)
    if role == "user" and approver and approver.startswith("agent:"):
        forms_html += f'''    <form method="post" action="/action" style="display:inline;">
        <input type="hidden" name="path" value="{html.escape(str(artifact_path))}">
        <input type="hidden" name="action" value="reopen">
        <button type="submit">Reopen</button>
    </form>\n'''

    forms_html += '</div>\n'
    return forms_html


def render_artifact(path_str, root, role=None, viewer_identity=None):
    """Render a single artifact view."""
    try:
        # Validate the path
        artifact_path = root / path_str
        check_inside_outputs(root, artifact_path)

        if not artifact_path.exists():
            return None, 404

        # Read the artifact
        with open(artifact_path, 'r') as f:
            content = f.read()

        # Parse header and body
        header = read_header(artifact_path)

        # Find where the body starts (after the closing ```)
        import re
        match = re.match(r"^```\n.*?\n```\n", content, re.DOTALL)
        body_text = content[match.end():] if match else content

        # Build header table
        header_html = '<table class="artifact-header"><tbody>'
        for key in ['issue', 'task', 'stage', 'status', 'author', 'approver', 'approved_at', 'tier', 'tier_suggested']:
            if key in header:
                value = header[key]
                header_html += f'<tr><td>{html.escape(key)}</td><td>{html.escape(value)}</td></tr>'
        header_html += '</tbody></table>'

        # Read reviews
        reviews = read_reviews(artifact_path)
        review_html = '<div class="reviews">'
        if reviews:
            review_html += '<h3>Review Thread</h3>'
            for review in reviews:
                review_html += f"""<div class="review-entry">
    <div class="review-header">{html.escape(review["ts"])} | {html.escape(review["kind"])} | {html.escape(review["who"])}</div>
    <div class="review-text">{html.escape(review["text"])}</div>
</div>"""
        review_html += '</div>'

        # Render action forms if role and viewer_identity are provided
        forms_html = ""
        if role and viewer_identity:
            forms_html = render_action_forms(artifact_path, header, role, viewer_identity)

        body = f"""
<div class="artifact-view">
    {header_html}
    <div class="artifact-body">
        <h2>{html.escape(artifact_path.name)}</h2>
        <pre>{html.escape(body_text)}</pre>
    </div>
    {forms_html}
    {review_html}
</div>
"""
        return body, 200
    except ValueError:
        # Path outside output folders
        return None, 403


# --- actions (WP8) ---
# --- end actions ---
# --- helper tab (WP9) ---

def render_helper(store, role):
    """Render the helper task list page."""
    if role != "helper":
        # Users can also view the helper page, but with limited actions
        pass

    tasks = store.list()

    html_parts = []
    html_parts.append('<div class="helper-list">')

    if not tasks:
        html_parts.append('<p>No helper tasks.</p>')
    else:
        for task in tasks:
            task_id = task.get("id", "")
            task_name = task.get("task", "")
            criterion = task.get("criterion", "")
            title = task.get("title", "")
            instructions = task.get("instructions", "")
            priority = task.get("priority", "")
            blocks_approval = task.get("blocks_approval", False)
            status = task.get("status", "")
            result = task.get("result", "")
            blocked_reason = task.get("blocked_reason", "")

            # Build the card
            badge_blocks = "blocks-approval" if blocks_approval else ""
            badge_class = f"badge {badge_blocks}" if badge_blocks else ""
            badge_html = f'<span class="{badge_class}">Blocks Approval</span>' if blocks_approval else ""

            status_badge = f'<span class="status-badge status-{status}">{html.escape(status)}</span>'

            html_parts.append(f"""
    <div class="helper-card">
        <div class="card-header">
            <span class="priority priority-{html.escape(priority)}">{html.escape(priority)}</span>
            <span class="task-info">{html.escape(task_name)} / {html.escape(criterion)}</span>
            {badge_html}
        </div>
        <div class="card-title">{html.escape(title)}</div>
        <div class="card-instructions">{html.escape(instructions)}</div>
        <div class="card-footer">
            {status_badge}
            <span class="task-id">{html.escape(task_id)}</span>
        </div>
""")

            # Blocked reason if applicable
            if status == "blocked" and blocked_reason:
                html_parts.append(f'        <div class="blocked-reason">Blocked: {html.escape(blocked_reason)}</div>\n')

            # Result if done
            if status == "done" and result:
                html_parts.append(f'        <div class="result">Result: {html.escape(result)}</div>\n')

            # Action forms
            html_parts.append('        <div class="card-actions">\n')

            if status == "todo":
                if role == "helper":
                    html_parts.append(f"""            <form method="post" action="/helper-action" class="action-form">
                <input type="hidden" name="action" value="start">
                <input type="hidden" name="task_id" value="{html.escape(task_id)}">
                <button type="submit" class="btn btn-start">Start</button>
            </form>
""")
                else:
                    # Users can't start tasks
                    html_parts.append('            <button class="btn btn-start" disabled>Start (helpers only)</button>\n')

            if status == "doing":
                if role == "helper":
                    html_parts.append(f"""            <form method="post" action="/helper-action" class="action-form">
                <input type="hidden" name="action" value="done">
                <input type="hidden" name="task_id" value="{html.escape(task_id)}">
                <textarea name="result" placeholder="Result..." required></textarea>
                <input type="text" name="path" placeholder="Optional file path">
                <button type="submit" class="btn btn-done">Done</button>
            </form>
            <form method="post" action="/helper-action" class="action-form">
                <input type="hidden" name="action" value="block">
                <input type="hidden" name="task_id" value="{html.escape(task_id)}">
                <textarea name="reason" placeholder="Reason..." required></textarea>
                <button type="submit" class="btn btn-block">Block</button>
            </form>
""")
                else:
                    html_parts.append('            <p>In progress</p>\n')

            if status == "blocked":
                if role == "user":
                    html_parts.append(f"""            <form method="post" action="/helper-action" class="action-form">
                <input type="hidden" name="action" value="unblock">
                <input type="hidden" name="task_id" value="{html.escape(task_id)}">
                <button type="submit" class="btn btn-unblock">Unblock</button>
            </form>
""")
                else:
                    html_parts.append('            <p>Blocked (users can unblock)</p>\n')

            if status == "done":
                html_parts.append('            <p>Completed</p>\n')

            html_parts.append('        </div>\n')
            html_parts.append('    </div>\n')

    html_parts.append('</div>')

    return '\n'.join(html_parts)

# --- end helper tab ---
# --- audit/evidence (WP10) ---

def render_audit(root):
    """Render the audit feed of agent approvals."""
    import re

    # Collect all approve entries by agents from all review files
    approvals = []

    for artifact_path in list_artifacts(root):
        review_path = artifact_path.with_name(artifact_path.stem + "-review.md")
        if not review_path.exists():
            continue

        reviews = read_reviews(artifact_path)
        for review in reviews:
            if review["kind"] == "approve" and review["who"].startswith("agent:"):
                # Check if the artifact is still approved
                try:
                    header = read_header(artifact_path)
                    is_still_approved = header.get("status") == "approved" and header.get("approver").startswith("agent:")
                except Exception:
                    is_still_approved = False

                approvals.append({
                    "ts": review["ts"],
                    "path": str(artifact_path),
                    "who": review["who"],
                    "is_still_approved": is_still_approved,
                })

    # Sort by timestamp, newest first
    approvals.sort(key=lambda x: x["ts"], reverse=True)

    # Build HTML
    html_parts = ['<div class="audit-feed">']
    if approvals:
        html_parts.append('<table class="audit-table">')
        for approval in approvals:
            artifact_link = f'/artifact?path={approval["path"]}'
            reopen_button = ""
            if approval["is_still_approved"]:
                reopen_button = f'''<form method="POST" action="/action" class="inline-form">
                    <input type="hidden" name="action" value="reopen">
                    <input type="hidden" name="path" value="{html.escape(approval["path"])}">
                    <button type="submit" class="btn-reopen">Reopen</button>
                </form>'''
            html_parts.append(f'''<tr>
    <td><a href="{artifact_link}">{html.escape(approval["path"])}</a></td>
    <td>{html.escape(approval["who"])}</td>
    <td>{html.escape(approval["ts"])}</td>
    <td>{reopen_button}</td>
</tr>''')
        html_parts.append('</table>')
    else:
        html_parts.append('<p>No agent approvals found.</p>')
    html_parts.append('</div>')

    return '\n'.join(html_parts)


def render_evidence(task, root):
    """Render evidence view for a task's acceptance criteria."""
    import re

    if not task:
        return None

    # Find the spec file for this task
    spec_path = None
    for artifact_path in list_artifacts(root):
        if artifact_path.name.endswith("-spec.md"):
            try:
                header = read_header(artifact_path)
                if header.get("task") == task:
                    spec_path = artifact_path
                    break
            except Exception:
                pass

    if not spec_path:
        return None

    # Parse criteria from spec file
    try:
        with open(spec_path, 'r') as f:
            content = f.read()
    except Exception:
        return None

    # Find "Acceptance Criteria" section and extract criteria
    criteria = {}
    in_criteria_section = False
    lines = content.split('\n')
    for line in lines:
        if 'Acceptance Criteria' in line:
            in_criteria_section = True
            continue
        if in_criteria_section:
            # Look for lines like "- [ ] AC1: ..." or "- [x] AC1: ..."
            match = re.match(r'^\s*-\s+\[.\]\s+(AC\d+):\s*(.*)', line)
            if match:
                ac_id, ac_text = match.groups()
                criteria[ac_id] = ac_text.strip()
            elif line.strip() and not line.startswith('-'):
                # End of criteria section
                break

    if not criteria:
        return None

    # Find evidence file (in 05-verify stage)
    evidence_data = {}
    # Extract the artifact number from the spec file name
    spec_name = spec_path.name
    # The name format is NN-task-spec.md, we need to construct NN-task-evidence.md
    base_name = spec_name.replace("-spec.md", "")
    evidence_path = root / "stages" / "05-verify" / "output" / f"{base_name}-evidence.md"
    if evidence_path.exists():
        try:
            with open(evidence_path, 'r') as f:
                content = f.read()
            # Parse table: | AC1 | status | notes |
            for line in content.split('\n'):
                match = re.match(r'^\|\s*(AC\d+)\s*\|\s*(\S+)\s*\|\s*(.*)\s*\|', line)
                if match:
                    ac_id, status, notes = match.groups()
                    evidence_data[ac_id] = status.strip()
        except Exception:
            pass

    # Get helper tasks for this criterion
    try:
        store = get_store(root, root)
        all_tasks = store.list(task=task)
        helper_status = {}
        for helper_task in all_tasks:
            if helper_task.get("status") == "done" and helper_task.get("criterion"):
                ac_id = helper_task["criterion"]
                helper_status[ac_id] = "met (helper task)"
    except Exception:
        helper_status = {}

    # Build HTML
    html_parts = ['<div class="evidence-view">']
    html_parts.append(f'<h2>Evidence for {html.escape(task)}</h2>')
    html_parts.append('<table class="evidence-table">')
    html_parts.append('<thead><tr><th>Criterion</th><th>Description</th><th>Status</th></tr></thead>')
    html_parts.append('<tbody>')

    for ac_id in sorted(criteria.keys(), key=lambda x: int(x[2:])):
        ac_text = criteria[ac_id]

        # Determine status
        if ac_id in helper_status:
            status = helper_status[ac_id]
        elif ac_id in evidence_data:
            status = evidence_data[ac_id]
            # If the evidence status is "unmapped", render it in bold
            if status == "unmapped":
                status = "<strong>unmapped</strong>"
        else:
            status = "<strong>unmapped</strong>"

        html_parts.append(f'''<tr>
    <td>{html.escape(ac_id)}</td>
    <td>{html.escape(ac_text)}</td>
    <td>{status}</td>
</tr>''')

    html_parts.append('</tbody>')
    html_parts.append('</table>')
    html_parts.append('</div>')

    return '\n'.join(html_parts)

# --- end audit/evidence ---
