"""
ICM GUI server using ThreadingHTTPServer.
"""

import urllib.parse
import argparse
import html
import sys
from dataclasses import dataclass, field
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from icmlib import default_root, default_project, load_people, parse_identity
from stage_status import collect
import helper as helper_module
import review

# Import views
try:
    from .views import shared_layout, render_queue, render_pipeline, render_artifact, render_helper, render_audit, render_evidence
except ImportError:
    from views import shared_layout, render_queue, render_pipeline, render_artifact, render_helper, render_audit, render_evidence


# Maximum size, in bytes, accepted for a POST body (form data).
MAX_BODY = 65536


@dataclass
class RequestContext:
    """Everything a route handler needs to answer one request."""

    root: Path
    project: Path
    viewer: str
    role: str
    path: str
    query: dict
    form: dict
    _status_data: object = field(default=None, repr=False, compare=False)

    @property
    def status_data(self):
        """Lazily computed task/artifact status, from stage_status.collect."""
        if self._status_data is None:
            self._status_data = collect(self.root, self.project)
        return self._status_data


class Redirect:
    """Marker returned by a handler that wants a 303 redirect instead of a body."""

    def __init__(self, location):
        self.location = location


def send_html(status, body):
    """Build a (status, html) result for a route handler to return."""
    return (status, body)


def redirect(location):
    """Build a 303-redirect result for a route handler to return."""
    return Redirect(location)


# --- base routes (WP7) ---

def handle_root(req):
    """GET / — the Queue page (users); helpers are sent to their own tab."""
    if req.role == "helper":
        return redirect("/helper")
    body = render_queue(req.status_data, req.root, req.role)
    if body is None:
        return send_html(403, "<h1>403 Forbidden</h1>")
    return send_html(200, shared_layout("Queue", body, req.role, req.viewer, "/"))


def handle_pipeline(req):
    """GET /pipeline — tasks x stages table."""
    body = render_pipeline(req.status_data, req.root)
    return send_html(200, shared_layout("Pipeline", body, req.role, req.viewer, "/pipeline"))


def handle_artifact(req):
    """GET /artifact?path=... — a single artifact's header, body and reviews."""
    path_arg = req.query.get("path", [""])[0]
    body, status_code = render_artifact(path_arg, req.root, req.role, req.viewer)
    if status_code == 403:
        return send_html(403, "<h1>403 Forbidden</h1>")
    if body is None:
        return send_html(404, "<h1>404 Not Found</h1>")
    return send_html(200, shared_layout("Artifact", body, req.role, req.viewer, "/artifact"))


GET_ROUTES = {
    "/": handle_root,
    "/pipeline": handle_pipeline,
    "/artifact": handle_artifact,
}

POST_ROUTES = {}

# Which roles may reach a given path. A path left out of this dict is open
# to every role; a role not listed for a path present here gets 403.
ROLE_ALLOWED = {
    "/": {"user", "helper", "agent"},
    "/pipeline": {"user", "helper", "agent"},
    "/artifact": {"user", "helper", "agent"},
}

# --- end base routes ---

# --- actions (WP8) ---

def handle_action(req):
    """POST /action — execute a review action via review.main."""
    action = req.form.get("action", "")
    path_arg = req.form.get("path", "")

    if not action or not path_arg:
        return send_html(400, "<h1>400 Bad Request</h1>")

    # Build the command for review.main
    cmd_args = [
        "--root", str(req.root),
        "--project", str(req.project),
        "--as", req.viewer,
        action,
        path_arg,
    ]

    # Add optional arguments based on the action
    if action in ("request-changes", "comment", "ask", "answer"):
        text = req.form.get("text", "")
        cmd_args.extend(["--text", text])
    elif action == "set-tier":
        tier = req.form.get("tier", "")
        cmd_args.append(tier)

    # Capture stderr from review.main
    import io
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        result = review.main(cmd_args)
        stderr_content = sys.stderr.getvalue()
    finally:
        sys.stderr = old_stderr

    # Determine the message
    if result == 0:
        msg = "Action completed"
    else:
        # Extract error message from stderr
        msg = stderr_content.strip().replace("error: ", "")

    # Redirect back to the artifact page with a message
    artifact_link = "/artifact?path=" + urllib.parse.quote(path_arg)
    if msg:
        artifact_link += "&msg=" + urllib.parse.quote_plus(msg)

    return redirect(artifact_link)


POST_ROUTES["/action"] = handle_action

# --- end actions ---
# --- helper tab (WP9) ---

def handle_helper(req):
    """GET /helper — the Helper task list page."""
    store = helper_module.get_store(req.root, req.project)
    body = render_helper(store, req.role)
    return send_html(200, shared_layout("Helper", body, req.role, req.viewer, "/helper"))


def handle_helper_action(req):
    """POST /helper-action — handle helper task actions."""
    action = req.form.get("action")
    task_id = req.form.get("task_id")

    if not action or not task_id:
        return send_html(400, "<h1>400 Bad Request</h1>")

    try:
        argv = ["--root", str(req.root), "--project", str(req.project), "--as", req.viewer]

        if action == "start":
            argv.extend(["start", task_id])
        elif action == "done":
            result = req.form.get("result", "")
            path = req.form.get("path", "")
            argv.extend(["done", task_id, "--result", result])
            if path:
                argv.extend(["--path", path])
        elif action == "block":
            reason = req.form.get("reason", "")
            argv.extend(["block", task_id, "--reason", reason])
        elif action == "unblock":
            argv.extend(["unblock", task_id])
        else:
            return send_html(400, "<h1>400 Bad Request</h1>")

        # Call helper.main with the arguments
        result_code = helper_module.main(argv)

        if result_code == 0:
            # Success: redirect back to helper page with success message
            return redirect("/helper?msg=success")
        else:
            # Failure: redirect back with error message
            return redirect("/helper?msg=error")
    except Exception as e:
        return redirect("/helper?msg=" + urllib.parse.quote_plus(str(e)))


GET_ROUTES["/helper"] = handle_helper
POST_ROUTES["/helper-action"] = handle_helper_action

ROLE_ALLOWED["/helper"] = {"user", "helper", "agent"}
ROLE_ALLOWED["/helper-action"] = {"user", "helper", "agent"}

# --- end helper tab ---
# --- audit/evidence (WP10) ---

def handle_audit(req):
    """GET /audit — audit feed of agent approvals (users)."""
    body = render_audit(req.root)
    if body is None:
        return send_html(403, "<h1>403 Forbidden</h1>")
    return send_html(200, shared_layout("Audit", body, req.role, req.viewer, "/audit"))


def handle_evidence(req):
    """GET /evidence?task=... — acceptance criteria and evidence (everyone)."""
    task_arg = req.query.get("task", [""])[0]
    body = render_evidence(task_arg, req.root)
    if body is None:
        return send_html(404, "<h1>404 Not Found</h1>")
    return send_html(200, shared_layout("Evidence", body, req.role, req.viewer, "/evidence"))


GET_ROUTES["/audit"] = handle_audit
GET_ROUTES["/evidence"] = handle_evidence

ROLE_ALLOWED["/audit"] = {"user", "agent"}
ROLE_ALLOWED["/evidence"] = {"user", "helper", "agent"}

# --- end audit/evidence ---


class ICMHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the ICM GUI."""

    def do_GET(self):
        """Parse the request, then dispatch to GET_ROUTES."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/static/"):
            self.serve_static(path)
            return

        query = parse_qs(parsed.query)
        req = self.make_context(path, query, {})
        self.dispatch(GET_ROUTES, req)

    def do_POST(self):
        """Parse the request (including a capped, urlencoded form body), then dispatch to POST_ROUTES."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            content_length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            content_length = 0

        read_length = min(content_length, MAX_BODY)
        raw_body = self.rfile.read(read_length) if read_length > 0 else b""

        # Drain and discard anything past the cap so the connection stays consistent.
        remaining = content_length - read_length
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            remaining -= len(chunk)

        form = {
            key: values[0]
            for key, values in parse_qs(raw_body.decode("utf-8", errors="replace")).items()
        }

        req = self.make_context(path, query, form)
        self.dispatch(POST_ROUTES, req)

    def make_context(self, path, query, form):
        """Build the RequestContext for one request from the server's configuration."""
        return RequestContext(
            root=self.server.root,
            project=self.server.project,
            viewer=self.server.viewer_identity,
            role=self.server.role,
            path=path,
            query=query,
            form=form,
        )

    def dispatch(self, routes, req):
        """Apply the role gate, find a handler for req.path, run it, and write the result."""
        allowed = ROLE_ALLOWED.get(req.path)
        if allowed is not None and req.role not in allowed:
            self.write_result(send_html(403, "<h1>403 Forbidden</h1>"))
            return

        handler = routes.get(req.path)
        if handler is None:
            self.write_result(send_html(404, "<h1>404 Not Found</h1>"))
            return

        try:
            result = handler(req)
        except Exception as e:
            result = send_html(500, f"<h1>500 Error</h1><p>{html.escape(str(e))}</p>")

        self.write_result(result)

    def write_result(self, result):
        """Write a handler's (status, html) or Redirect result to the client."""
        if isinstance(result, Redirect):
            self.send_response(303)
            self.send_header("Location", result.location)
            self.end_headers()
            return

        status, body = result
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_static(self, path):
        """Serve static files from gui/static/, resolved relative to this file."""
        if path == "/static/style.css":
            static_path = Path(__file__).resolve().parent / "static" / "style.css"
            if static_path.exists():
                with open(static_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/css")
                self.end_headers()
                self.wfile.write(content)
                return

        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>404 Not Found</h1>")

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def main(argv=None):
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="ICM GUI server")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--root", type=Path, default=None, help="Root directory")
    parser.add_argument("--project", type=Path, default=None, help="Project directory")
    parser.add_argument("--as", dest="viewer", required=True, help="Viewer identity (e.g., user:user1)")

    args = parser.parse_args(argv)

    # Set defaults
    if args.root is None:
        args.root = default_root()
    if args.project is None:
        args.project = default_project(args.root)

    args.root = Path(args.root)
    args.project = Path(args.project)

    # Validate identity
    try:
        kind, name, model = parse_identity(args.viewer)
    except ValueError as e:
        print(f"Error: invalid identity: {e}", file=sys.stderr)
        return 1

    # Check if user/helper is in people.md
    if kind in ("user", "helper"):
        people = load_people(args.project)
        if name not in people or people[name] != kind:
            print(f"Error: unknown {kind} {name}", file=sys.stderr)
            return 1
        role = kind
    else:
        role = "agent"

    # Collect status data
    status_data = collect(args.root, args.project)

    # Create and configure server
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ICMHandler)
    server.root = args.root
    server.project = args.project
    server.viewer = args.viewer
    server.viewer_identity = args.viewer
    server.status_data = status_data
    server.role = role

    print(f"Serving on http://127.0.0.1:{args.port}/", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())
