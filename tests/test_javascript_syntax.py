import shutil
import subprocess
from pathlib import Path
import pytest

def test_app_javascript_parses():
    node = shutil.which('node')
    if not node:
        pytest.skip('node is not installed; skipping JavaScript syntax check')
    result = subprocess.run([node, '--check', str(Path('static/app.js'))], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
