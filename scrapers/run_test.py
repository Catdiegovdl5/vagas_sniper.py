import sys
import os

# Add parent directory to path to allow importing scrapers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers import linkedin, glassdoor, infojobs, indeed, jooble

def test_job_contract(job, platform_name):
    # Required keys in standard schema
    required_keys = ["platform", "title", "company", "budget", "link", "job_type", "profession", "level", "requirements"]
    
    for key in required_keys:
        assert key in job, f"Missing key '{key}' in job from {platform_name}"
        assert job[key] is not None, f"Key '{key}' is None in job from {platform_name}"
        assert isinstance(job[key], str), f"Key '{key}' is not a string in job from {platform_name}"

    assert len(job["title"]) > 0, f"Title is empty in job from {platform_name}"
    assert len(job["company"]) > 0, f"Company is empty in job from {platform_name}"
    assert len(job["requirements"]) > 0, f"Requirements (description) is empty in job from {platform_name}"
    
    if platform_name == "LinkedIn":
        # Check LinkedIn specific constraint: description (requirements) >= 500 characters
        assert len(job["requirements"]) >= 500, f"LinkedIn job description is too short ({len(job['requirements'])} chars)"
        # Check LinkedIn full-time check: must contain "tempo integral" or "full-time" or similar in text (case-insensitive)
        text_to_check = job["requirements"].lower()
        has_fulltime = "tempo integral" in text_to_check or "full-time" in text_to_check or "full time" in text_to_check
        assert has_fulltime, f"LinkedIn job is not full-time: {job['requirements'][:100]}..."

    print(f"  [PASS] Contract verified for job: '{job['title']}' at '{job['company']}'")

def run_tests():
    scrapers = {
        "LinkedIn": linkedin.scrape,
        "Glassdoor": glassdoor.scrape,
        "Infojobs": infojobs.scrape,
        "Indeed": indeed.scrape,
        "Jooble": jooble.scrape
    }
    
    keyword = "Python"
    level = "Todos"
    country = "Brasil"
    
    print("=== STARTING SCRAPERS VERIFICATION TEST ===")
    print(f"Query parameters: keyword='{keyword}', level='{level}', country='{country}'\n")
    
    all_passed = True
    
    for name, scrape_func in scrapers.items():
        print(f"\n--- Testing Scraper: {name} ---")
        try:
            results = scrape_func(keyword, level=level, country=country)
            
            # Jooble might return a dummy job if empty, which has title containing "Sem vagas"
            # We ignore dummy jobs or empty lists for contract verification
            valid_results = [r for r in results if "Sem vagas" not in r["title"] and "Não houve" not in r["requirements"]]
            
            print(f"Total jobs returned: {len(results)} (Valid/Filtered: {len(valid_results)})")
            
            if not valid_results:
                print(f"  [WARN] No valid jobs returned by {name} (this is normal if no jobs are listed or bot protection blocks the request)")
                continue
                
            for idx, job in enumerate(valid_results[:3]): # test up to top 3 jobs to verify contract
                print(f" Verifying job #{idx+1}...")
                test_job_contract(job, name)
                
        except Exception as e:
            print(f"  [FAIL] {name} scraper raised an exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            
    print("\n===========================================")
    if all_passed:
        print("VERIFICATION COMPLETED. ALL ACTIVE TESTS PASSED.")
        sys.exit(0)
    else:
        print("VERIFICATION COMPLETED. SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
