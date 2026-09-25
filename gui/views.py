"""
Views for the ICM GUI server.
"""

import html
from pathlib import Path
from urllib.parse import urlencode, parse_qs

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from icmlib import check_inside_outputs, read_header, read_reviews


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

        html_parts.append(f'<tr><td class="task-name">{html.escape(task_name)}</td>')
        html_parts.append(f'<td>{html.escape(tier)}</td>')

        for stage in stages:
            artifact = task_stage_map.get(task_name, {}).get(stage)
            if artifact:
                artifact_link = f'/artifact?path={artifact["path"]}'
                html_parts.append(f'<td><a href="{artifact_link}">{html.escape(artifact["checkpoint"])}</a></td>')
            else:
                html_parts.append('<td>—</td>')

        html_parts.append('</tr>')

    html_parts.append('</tbody>')
    html_parts.append('</table>')

    body = '\n'.join(html_parts)
    return body


def render_artifact(path_str, root):
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

        body = f"""
<div class="artifact-view">
    {header_html}
    <div class="artifact-body">
        <h2>{html.escape(artifact_path.name)}</h2>
        <pre>{html.escape(body_text)}</pre>
    </div>
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
# --- end helper tab ---
# --- audit/evidence (WP10) ---
# --- end audit/evidence ---
