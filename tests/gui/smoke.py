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

            # Try to access queue as helper
            url = f"http://127.0.0.1:{port}/"
            try:
                response = urllib.request.urlopen(url)
                assert response.status == 403
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
