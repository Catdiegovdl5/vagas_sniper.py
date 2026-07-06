import sqlite3
import os
import requests

def apply_to_job(job_link: str, resume_path: str, mock_ats_url: str = None) -> bool:
    """
    Submits a job application with the resume PDF to the local mock ATS server.
    """
    if not mock_ats_url:
        mock_ats_url = os.getenv("MOCK_ATS_URL", "http://127.0.0.1:8081/apply")

    if not os.path.exists(resume_path):
        # Create a dummy file if it doesn't exist
        with open(resume_path, "wb") as f:
            f.write(b"%PDF-1.4 Mock PDF Content")

    try:
        with open(resume_path, "rb") as f:
            files = {"resume": (os.path.basename(resume_path), f, "application/pdf")}
            data = {
                "job_link": job_link,
                "name": "Diego Candidate",
                "email": "diego@example.com"
            }
            # Post to the mock ATS server
            response = requests.post(mock_ats_url, data=data, files=files, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                return res_data.get("status") == "success"
            return False
    except Exception as e:
        print(f"Error during auto-apply HTTP request to {mock_ats_url}: {e}")
        return False

def run_auto_apply(db_path: str, resume_path: str, mock_ats_url: str = None) -> int:
    """
    Main entry point for mock auto-apply.
    Selects high-scoring pending/approved jobs from the db and submits them.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Ensure tables and columns exist
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'pending'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN score INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # Find jobs with score >= 80 and status 'pending' (or null)
    c.execute("SELECT link FROM jobs WHERE score >= 80 AND (status = 'pending' OR status IS NULL)")
    jobs = c.fetchall()
    
    applied_count = 0
    for (link,) in jobs:
        success = apply_to_job(link, resume_path, mock_ats_url)
        new_status = "applied" if success else "failed"
        c.execute("UPDATE jobs SET status = ? WHERE link = ?", (new_status, link))
        conn.commit()
        if success:
            applied_count += 1
            
    conn.close()
    return applied_count
