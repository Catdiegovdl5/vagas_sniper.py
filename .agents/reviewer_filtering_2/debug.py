import sys
import os
import sqlite3

# Add project root to path
sys.path.append(r"C:\Users\99196\OneDrive\Documentos\vagas_bot")

import database

# Monkeypatch
TEST_DB_PATH = r"C:\Users\99196\OneDrive\Documentos\vagas_bot\tests\jobs_test.db"
database.DB_PATH = TEST_DB_PATH

# Initialize database
database.init_db()

# Verify DB_PATH
print("database.DB_PATH:", database.DB_PATH)

# Insert job
conn = sqlite3.connect(database.DB_PATH)
c = conn.cursor()
c.execute(
    "INSERT INTO jobs (id, title, company, budget, link, platform, requirements) VALUES (?, ?, ?, ?, ?, ?, ?)",
    ("https://example.com/job/dash-test-1", "Dashboard Engineer", "Dash Corp", "R$ 7.000", "https://example.com/job/dash-test-1", "LinkedIn", "Requirements for dashboard test")
)
conn.commit()
print("Inserted manually. Rows in DB:")
c.execute("SELECT * FROM jobs")
print(c.fetchall())
conn.close()

# Now import app and client
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

response = client.get("/api/jobs")
print("Response status:", response.status_code)
print("Response data:", response.json())
