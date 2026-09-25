"""
ICM GUI server using ThreadingHTTPServer.
"""

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

# Import views
try:
    from .views import shared_layout, render_queue, render_pipeline, render_artifact
except ImportError:
    from views import shared_layout, render_queue, render_pipeline, render_artifact


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
    """GET / — the Queue page (users)."""
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
    body, status_code = render_artifact(path_arg, req.root)
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
    "/": {"user", "agent"},
    "/pipeline": {"user", "helper", "agent"},
    "/artifact": {"user", "helper", "agent"},
}

# --- end base routes ---

# --- actions (WP8) ---
# --- end actions ---
# --- helper tab (WP9) ---
# --- end helper tab ---
# --- audit/evidence (WP10) ---
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
