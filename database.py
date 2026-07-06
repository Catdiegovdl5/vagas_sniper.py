import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            budget TEXT,
            link TEXT,
            platform TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try: c.execute('ALTER TABLE jobs ADD COLUMN job_type TEXT')
    except: pass
    try: c.execute('ALTER TABLE jobs ADD COLUMN profession TEXT')
    except: pass
    try: c.execute('ALTER TABLE jobs ADD COLUMN level TEXT')
    except: pass
    try: c.execute('ALTER TABLE jobs ADD COLUMN requirements TEXT')
    except: pass
    conn.commit()
    conn.close()

def insert_jobs(jobs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    inserted = 0
    for job in jobs:
        try:
            c.execute('INSERT INTO jobs (id, title, company, budget, link, platform, job_type, profession, level, requirements) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (job['link'], job['title'], job.get('company', 'N/A'), job.get('budget', 'A combinar'), job['link'], job['platform'], job.get('job_type', 'CLT'), job.get('profession', 'Tech'), job.get('level', 'ND'), job.get('requirements', 'Requisitos descritos no link da vaga.')))
            inserted += 1
        except sqlite3.IntegrityError:
            pass # duplicate
    conn.commit()
    conn.close()
    return inserted

def get_jobs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title, company, budget, link, platform, added_at, job_type, profession, level, requirements FROM jobs ORDER BY added_at DESC')
    rows = c.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        jobs.append({
            "title": r[0],
            "company": r[1],
            "budget": r[2],
            "link": r[3],
            "platform": r[4],
            "added_at": r[5],
            "job_type": r[6] if len(r)>6 else "CLT",
            "profession": r[7] if len(r)>7 else "Tech",
            "level": r[8] if len(r)>8 else "ND",
            "requirements": r[9] if len(r)>9 else "Requisitos na página."
        })
    return jobs

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

# Alias para compatibilidade
get_all_jobs = get_jobs

