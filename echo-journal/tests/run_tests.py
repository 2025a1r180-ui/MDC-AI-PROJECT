"""
Test Runner for Echo Journal (Milestone 1).
Discovers and executes all tests in the tests/ directory.
Works on Windows, Linux, and macOS without external dependencies.
"""

import sys
import unittest
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    print("=" * 70)
    print("ECHO JOURNAL — ALL MILESTONES (1 THROUGH 6) VERIFICATION TEST SUITE")
    print("Validating: Private Foundation, BiLSTM Emotion Model, Hybrid Retrieval RAG,")
    print("            Aggregate-Only Admin & Production Hardening")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(Path(__file__).parent), pattern="test_*.py")
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.time() - start_time
    
    print("-" * 70)
    print(f"Tests Run:      {result.testsRun}")
    print(f"Failures:       {len(result.failures)}")
    print(f"Errors:         {len(result.errors)}")
    print(f"Execution Time: {elapsed:.3f}s")
    
    if result.wasSuccessful():
        print("\n>>> ALL TESTS PASSED: MILESTONE 1 FOUNDATION VERIFIED <<<")
        print("Account isolation, scrypt hashing, CSRF, and data export confirmed.")
        sys.exit(0)
    else:
        print("\n>>> TESTS FAILED: Please inspect errors above <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
