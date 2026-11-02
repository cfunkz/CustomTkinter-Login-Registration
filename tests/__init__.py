import os
import tempfile

# Use a throwaway SQLite database and fast hashing for the tests, set before config.py is imported
TEST_DIR = tempfile.mkdtemp(prefix="titleplacement-tests-")
os.environ["DATABASE_TYPE"] = "sqlite"
os.environ["DATABASE_FILE"] = os.path.join(TEST_DIR, "test.db")
os.environ["HASH_ITERATIONS"] = "1000"
os.environ["XDG_DATA_HOME"] = TEST_DIR
os.environ["APPDATA"] = TEST_DIR
