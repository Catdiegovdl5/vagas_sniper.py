import os
import sys
import pytest

def clean_and_test():
    print("==================================================")
    print("Cleaning unused scrapers and running tests...")
    print("==================================================")
    
    files_to_delete = [
        "scrapers/catho.py",
        "scrapers/gupy.py",
        "scrapers/trampos.py"
    ]
    
    for f_path in files_to_delete:
        abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                print(f"Deleted: {f_path}")
            except Exception as e:
                print(f"Failed to delete {f_path}: {e}")
        else:
            print(f"Already deleted: {f_path}")
            
    # Run pytest
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    args = ["-v", "-p", "no:warnings", tests_dir]
    print(f"Executing: pytest {' '.join(args)}\n")
    
    exit_code = pytest.main(args)
    print(f"Test Suite Finished with Exit Code: {exit_code}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    clean_and_test()
