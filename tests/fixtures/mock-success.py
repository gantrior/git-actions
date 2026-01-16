#!/usr/bin/env python3
"""Mock action script for testing.

This script simulates a successful action execution.
It reads JSON from stdin and writes success response to stdout.
"""

import sys
import json

def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)
    
    # Extract action details
    action = input_data.get("action")
    version = input_data.get("version")
    inputs = input_data.get("inputs", {})
    
    # Simulate successful execution
    output = {
        "status": "success",
        "outputs": {
            "result": "Mock execution successful",
            "action": action,
            "version": version,
            "input_count": len(inputs)
        }
    }
    
    # Write output to stdout
    json.dump(output, sys.stdout)
    sys.stdout.flush()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
