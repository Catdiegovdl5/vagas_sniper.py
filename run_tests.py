import sys
import pytest
import os

def run():
    print("==================================================")
    print("Starting E2E Test Suite Runner for vagas_bot")
    print("==================================================")
    
    # Path to tests directory
    tests_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
    
    # Arguments to pass to pytest:
    # -v: verbose output
    # -o log_cli=true: print logs to stdout
    # -p no:warnings: suppress warnings for clean output
    args = ["-v", "-p", "no:warnings", tests_dir]
    
    print(f"Executing: pytest {' '.join(args)}\n")
    
    # Run pytest
    exit_code = pytest.main(args)
    
    print("\n==================================================")
    print(f"Test Suite Finished with Exit Code: {exit_code}")
    print("==================================================")
    
    # Return 0 if exit code is pytest.ExitCode.OK (which is 0)
    if exit_code == 0:
        sys.exit(0)
    else:
        sys.exit(exit_code)

if __name__ == "__main__":
    run()
