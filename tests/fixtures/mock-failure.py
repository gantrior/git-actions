#!/usr/bin/env python3
"""Mock action script that fails.

This script simulates a failed action execution.
"""

import json
import sys


def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)

    # Simulate failure
    output = {"status": "error", "outputs": {}, "error": "Mock action failed: simulated error"}

    # Write output to stdout
    json.dump(output, sys.stdout)
    sys.stdout.flush()

    return 1


if __name__ == "__main__":
    sys.exit(main())
