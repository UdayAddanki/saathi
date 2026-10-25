import os
import tempfile
from pathlib import Path

# Test processes never open the developer's real database. This is set while
# conftest is imported, before app.db reads SAATHI_DB_PATH.
TEST_DB_DIR = Path(tempfile.mkdtemp(prefix='saathi-tests-'))
os.environ['SAATHI_DB_PATH'] = str(TEST_DB_DIR / 'test.db')
