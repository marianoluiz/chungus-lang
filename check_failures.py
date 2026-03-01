#!/usr/bin/env python3
"""Check failed test rows and show expected vs actual."""

import subprocess
import re

# Get all failed rows
result = subprocess.run(
    ["python", "-m", "pytest", "test/semantic/test_semantic.py", "--tb=line", "-q"],
    capture_output=True,
    text=True
)

failed_rows = []
for line in result.stdout.split('\n'):
    match = re.search(r'row(\d+)', line)
    if match and 'FAILED' in line:
        failed_rows.append(int(match.group(1)))

print(f"Total failures: {len(failed_rows)}\n")

# Check first 10 failures in detail
for row in failed_rows[:10]:
    result = subprocess.run(
        ["python", "-m", "pytest", f"test/semantic/test_semantic.py::test_semantic[row{row}]", 
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    # Extract expected and actual
    expected = None
    actual = None
    for line in result.stdout.split('\n'):
        if 'EXPECTED:' in line:
            match = re.search(r"EXPECTED: '([^']+)'", line)
            if match:
                expected = match.group(1)
        if 'ACTUAL:' in line:
            match = re.search(r"ACTUAL:\s+'([^']*)'", line)
            if match:
                actual = match.group(1)
    
    if expected and actual is not None:
        print(f"Row {row}:")
        print(f"  Expected: {expected[:80]}")
        print(f"  Actual:   {actual[:80] if actual else '(no error)'}")
        print()
