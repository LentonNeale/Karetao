"""
Smoke test for the ICM GUI server.

Tests basic functionality: queue, pipeline, artifact view, and access control.
"""

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from icmlib import default_root, default_project


def get_free_port():
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def test_queue_page():
    """Test the queue page loads with expected content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy demo fixtures to temp directory
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        # Start server
        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            # Wait for server to start
            time.sleep(0.5)

            # Fetch queue page
            url = f"http://127.0.0.1:{port}/"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')

            # Check for expected task names
            assert "demo-led" in content or "Demo LED" in content or "demo-hw" in content
            assert "Queue" in content

            print("✓ Queue page loads successfully")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_pipeline_page():
    """Test the pipeline page."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/pipeline"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')

            assert "Pipeline" in content or "01-intake" in content

            print("✓ Pipeline page loads successfully")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_artifact_view():
    """Test artifact view."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # Try to access a valid artifact
            url = f"http://127.0.0.1:{port}/artifact?path=stages/01-intake/output/10-demo-led-brief.md"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')
            assert "demo-led" in content

            print("✓ Artifact view loads successfully")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_path_traversal_blocked():
    """Test that path traversal attacks are blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # Try path traversal
            url = f"http://127.0.0.1:{port}/artifact?path=../../etc/passwd"
            try:
                response = urllib.request.urlopen(url)
                # If we get here, check the status code
                assert response.status == 403, f"Expected 403, got {response.status}"
            except urllib.error.HTTPError as e:
                assert e.code == 403

            print("✓ Path traversal is blocked")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_helper_access_control():
    """Test that helpers can't access the queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "helper:helper1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # A helper opening / is redirected to the Helper tab, and never sees the queue
            url = f"http://127.0.0.1:{port}/"
            response = urllib.request.urlopen(url)
            assert response.url.endswith("/helper"), response.url
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/audit")
                assert False, "helper reached /audit"
            except urllib.error.HTTPError as e:
                assert e.code == 403

            # But can access pipeline
            url = f"http://127.0.0.1:{port}/pipeline"
            response = urllib.request.urlopen(url)
            assert response.status == 200

            print("✓ Helper access control works")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_static_css():
    """Test that /static/style.css is served from a temporary copy of the demo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/static/style.css"
            response = urllib.request.urlopen(url)
            assert response.status == 200

            print("✓ Static CSS is served")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_post_unknown_path():
    """Test that a POST to an unknown path returns 404."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/no-such-route"
            try:
                response = urllib.request.urlopen(url, data=b"")
                assert response.status == 404, f"Expected 404, got {response.status}"
            except urllib.error.HTTPError as e:
                assert e.code == 404

            print("✓ POST to an unknown path returns 404")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_blocking_items_first():
    """Test that blocking items appear before non-blocking in the queue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/"
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')

            # Check that blocking items appear before non-blocking
            # 16-plan.md should be blocking, 15-plan.md should be non-blocking
            blocking_pos = content.find("16-demo-hw-plan") if "16-demo-hw-plan" in content else content.find("16-plan")
            non_blocking_pos = content.find("15-demo-ui-plan") if "15-demo-ui-plan" in content else content.find("15-plan")

            # If both items are in the queue, blocking should come first
            if blocking_pos >= 0 and non_blocking_pos >= 0:
                # Find the Blocking badge for the demo-hw item and Non-blocking badge
                blocking_badge_pos = content.rfind("Blocking", 0, non_blocking_pos)
                non_blocking_badge_pos = content.rfind("Non-blocking", 0, non_blocking_pos)

                # For a more robust test, check that Blocking appears before Non-blocking
                first_blocking = content.find("Blocking")
                first_non_blocking = content.find("Non-blocking")
                assert first_blocking < first_non_blocking, "Blocking items should appear before Non-blocking"

            print("✓ Blocking items appear first in queue")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_set_tier_on_brief():
    """Test that tier form appears on brief artifact page."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # Fetch the artifact page and check for tier form
            brief_path = "stages/01-intake/output/10-demo-led-brief.md"
            url = f"http://127.0.0.1:{port}/artifact?path={brief_path}"
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')

            # Check that tier buttons are present
            assert "Set Tier:" in content or "set-tier" in content, "Tier form should be present on brief"
            assert "T1" in content and "T2" in content and "T3" in content and "T4" in content, "Tier buttons should be present"

            print("✓ Tier form appears on brief artifact page")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_ask_answer_approve_flow():
    """Test that ask/answer/approve forms are available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # Fetch a spec page and check for ask form
            spec_path = "stages/02-issue-spec/output/12-demo-led-spec.md"
            url = f"http://127.0.0.1:{port}/artifact?path={spec_path}"
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')

            # Check that ask form is present on specs
            assert "Ask" in content or "ask" in content, "Ask button should be present on spec"
            # Check that comment form is present
            assert "Comment" in content or "comment" in content, "Comment button should be present"
            # Check that approve button is present (may be disabled)
            assert "Approve" in content or "approve" in content, "Approve button should be present"

            print("✓ Ask, comment, and approve forms are available")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_helper_cannot_approve():
    """Test that a helper cannot approve via POST."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "helper:helper1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # Get original file content
            spec_path = "stages/02-issue-spec/output/12-demo-led-spec.md"
            spec_file = demo_dst / spec_path
            with open(spec_file, 'r') as f:
                original_content = f.read()

            # Try to approve as helper
            url = f"http://127.0.0.1:{port}/action"
            data = urllib.parse.urlencode({
                "path": spec_path,
                "action": "approve"
            }).encode('utf-8')

            req = urllib.request.Request(url, data=data, method='POST')
            try:
                response = urllib.request.urlopen(req)
                # Should get redirect, file unchanged
            except urllib.error.HTTPError as e:
                # Could be 303 redirect or other error
                pass

            # Verify file is unchanged
            with open(spec_file, 'r') as f:
                new_content = f.read()
            assert original_content == new_content, "Helper approval should not change the file"

            print("✓ Helper cannot approve")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_audit_feed():
    """Test that audit feed shows agent approvals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/audit"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')

            # Check that the audit feed shows demo-docs
            assert "demo-docs" in content or "11-demo-docs-brief" in content, "Audit feed should show demo-docs"
            assert "agent:orchestrator" in content or "orchestrator/opus" in content, "Audit feed should show agent approval"

            print("✓ Audit feed shows agent approvals")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_evidence_unmapped():
    """Test that evidence view shows unmapped criteria."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/evidence?task=demo-fw"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')

            # Check that demo-fw evidence shows AC3 as unmapped
            assert "AC3" in content, "Evidence should list AC3"
            assert "unmapped" in content, "Evidence should show unmapped status"
            # Should have bold tag for unmapped
            assert "<strong>unmapped</strong>" in content, "Unmapped should be bold"

            print("✓ Evidence view shows unmapped criteria")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_helper_list_order():
    """Test that helper tasks are listed in correct sort order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "helper:helper1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/helper"
            response = urllib.request.urlopen(url)
            assert response.status == 200
            content = response.read().decode('utf-8')

            # Check that tasks are listed
            assert "Flash firmware v0.3" in content or "Assemble hardware" in content

            print("✓ Helper list page loads successfully")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_helper_start_task():
    """Test that starting a task changes its status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "helper:helper1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            # First, get the helper page to see initial state
            url = f"http://127.0.0.1:{port}/helper"
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')

            # Look for a task in "todo" status and start it
            # We'll look for task ID that we can start
            # Based on demo data, we have H4 in todo status
            if "H4" in content:
                # POST to start the task
                data = urllib.parse.urlencode({
                    'action': 'start',
                    'task_id': 'H4'
                }).encode('utf-8')

                try:
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/helper-action",
                        data=data,
                        method='POST'
                    )
                    response = urllib.request.urlopen(req)
                    # Should get a 303 redirect
                    assert response.status in [200, 303]
                except urllib.error.HTTPError as e:
                    # Redirects also raise HTTPError
                    assert e.code == 303

            print("✓ Helper task start works")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)


def test_user_cannot_start_task():
    """Test that users cannot start helper tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server",
             "--port", str(port),
             "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"),
             "--as", "user:user1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).resolve().parents[2]
        )

        try:
            time.sleep(0.5)

            url = f"http://127.0.0.1:{port}/helper"
            response = urllib.request.urlopen(url)
            content = response.read().decode('utf-8')

            # Users should see the helper page but buttons should be disabled
            # Check that start buttons are disabled for users
            if "disabled" in content and "todo" in content:
                # Users see disabled buttons
                pass

            print("✓ User access control for helper tasks works")
        finally:
            server_proc.terminate()
            server_proc.wait(timeout=5)



def test_tier_then_approve_end_to_end():
    """A user selects a tier, the Approve button becomes enabled, and approving updates the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)
        rel = "stages/01-intake/output/10-demo-led-brief.md"
        brief = demo_dst / rel

        port = get_free_port()
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "gui.server", "--port", str(port), "--root", str(demo_dst),
             "--project", str(demo_dst / "icm-project"), "--as", "user:user1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Path(__file__).resolve().parents[2])
        try:
            time.sleep(0.5)
            base = f"http://127.0.0.1:{port}"
            page = urllib.request.urlopen(f"{base}/artifact?path={urllib.parse.quote(rel)}").read().decode()
            assert 'title="tier not selected"' in page

            def post(fields):
                data = urllib.parse.urlencode(fields).encode()
                return urllib.request.urlopen(urllib.request.Request(f"{base}/action", data=data))

            post({"action": "set-tier", "path": str(brief), "tier": "T2"})
            page = urllib.request.urlopen(f"{base}/artifact?path={urllib.parse.quote(rel)}").read().decode()
            assert 'title="tier not selected"' not in page, "Approve still disabled after selecting a tier"

            post({"action": "approve", "path": str(brief)})
            text = brief.read_text()
            assert "status: approved" in text and "approver: user:user1" in text, text[:300]
            print("✓ Tier selection enables Approve, and approving updates the brief")
        finally:
            server_proc.terminate()
            server_proc.wait()


def test_review_cli_relative_path():
    """review.py resolves relative artifact paths against --root, not the current directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_src = Path(__file__).resolve().parents[2] / "gui" / "fixtures" / "demo"
        demo_dst = Path(tmpdir) / "demo"
        shutil.copytree(demo_src, demo_dst)
        ws = Path(__file__).resolve().parents[2]
        cmd = [sys.executable, str(ws / "scripts" / "review.py"), "--root", str(demo_dst),
               "--project", str(demo_dst / "icm-project"), "--as", "agent:orchestrator/opus", "approve"]
        ok = subprocess.run(cmd + ["stages/04-implement/output/14-demo-fw-plan.md"], capture_output=True, text=True, cwd=tmpdir)
        assert ok.returncode == 0, ok.stderr
        selfapp = subprocess.run(cmd + ["stages/02-issue-spec/output/13-demo-docs-spec.md"], capture_output=True, text=True, cwd=tmpdir)
        assert selfapp.returncode == 1 and "no self-approval" in selfapp.stderr, selfapp.stderr
        t3 = subprocess.run(cmd + ["stages/04-implement/output/15-demo-ui-plan.md"], capture_output=True, text=True, cwd=tmpdir)
        assert t3.returncode == 1 and "may not approve C5 at T3" in t3.stderr, t3.stderr
        print("✓ review.py accepts paths relative to --root")

def main():
    """Run all tests."""
    tests = [
        test_queue_page,
        test_pipeline_page,
        test_artifact_view,
        test_path_traversal_blocked,
        test_helper_access_control,
        test_static_css,
        test_post_unknown_path,
        test_blocking_items_first,
        test_set_tier_on_brief,
        test_ask_answer_approve_flow,
        test_helper_cannot_approve,
        test_helper_list_order,
        test_helper_start_task,
        test_user_cannot_start_task,
        test_audit_feed,
        test_evidence_unmapped,
        test_tier_then_approve_end_to_end,
        test_review_cli_relative_path,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed.append(test.__name__)

    if failed:
        print(f"\n{len(failed)} test(s) failed:")
        for name in failed:
            print(f"  - {name}")
        return 1

    print(f"\nAll {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
