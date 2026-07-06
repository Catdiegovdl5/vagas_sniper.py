import os
import sqlite3
import sys

# Add tests directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "tests"))
sys.path.append(os.path.dirname(__file__))

import database
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "tests", "jobs_test_reproduce.db")
database.DB_PATH = TEST_DB_PATH

# Initialize DB
database.init_db()
conn = sqlite3.connect(TEST_DB_PATH)
c = conn.cursor()
# Ensure table columns exist
cols = [
    ("score", "INTEGER"),
    ("status", "TEXT"),
    ("reason", "TEXT")
]
for col_name, col_type in cols:
    try:
        c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
    except sqlite3.OperationalError:
        pass
c.execute("DELETE FROM jobs")
conn.commit()
conn.close()

# Now import mock_auto_apply
import mock_auto_apply as aa

# Test case
conn = sqlite3.connect(database.DB_PATH)
c = conn.cursor()
c.execute(
    "INSERT INTO jobs (id, title, company, budget, link, platform, requirements, score, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    ("https://example.com/job/fail-test", "Python Expert", "Fail Corp", "R$ 15.000,00", "https://example.com/job/fail-test", "Glassdoor", "Mock requirements", 95, "pending")
)
conn.commit()
conn.close()

print("Inserted job. Querying before run_auto_apply:")
conn = sqlite3.connect(database.DB_PATH)
c = conn.cursor()
c.execute("SELECT * FROM jobs WHERE link = ?", ("https://example.com/job/fail-test",))
print(c.fetchone())
conn.close()

# Run with bad port
applied = aa.run_auto_apply(database.DB_PATH, "temp_curriculo.pdf", "http://127.0.0.1:8888/apply")
print(f"Applied: {applied}")

print("Querying after run_auto_apply:")
conn = sqlite3.connect(database.DB_PATH)
c = conn.cursor()
c.execute("SELECT status FROM jobs WHERE link = ?", ("https://example.com/job/fail-test",))
row = c.fetchone()
print(row)
conn.close()

# Clean up
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
