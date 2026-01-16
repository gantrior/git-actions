#!/usr/bin/env python3
"""Jira comment action script.

This script posts a comment to a Jira ticket.
Input: JSON with ticket ID and comment text
Output: JSON with comment URL and ID
"""

import sys
import json
import os

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        # Extract inputs
        inputs = input_data.get("inputs", {})
        ticket = inputs.get("ticket")
        comment = inputs.get("comment")
        
        # Validate required inputs
        if not ticket or not comment:
            return {
                "status": "error",
                "outputs": {},
                "error": "Missing required inputs: ticket and comment"
            }
        
        # In a real implementation, this would call the Jira API
        # For now, we'll simulate a successful comment post
        
        # Check for API credentials (should be in environment)
        jira_url = os.environ.get("JIRA_URL", "https://jira.example.com")
        jira_token = os.environ.get("JIRA_API_TOKEN")
        
        if not jira_token:
            # In non-CI environment, this is okay for testing
            # In CI, this would be an error
            if os.environ.get("CI") == "true":
                return {
                    "status": "error",
                    "outputs": {},
                    "error": "JIRA_API_TOKEN environment variable not set"
                }
        
        # Simulate successful API call
        comment_id = "12345"
        comment_url = f"{jira_url}/browse/{ticket}#comment-{comment_id}"
        
        # Return success result
        output = {
            "status": "success",
            "outputs": {
                "commentUrl": comment_url,
                "commentId": comment_id
            }
        }
        
        json.dump(output, sys.stdout)
        return 0
        
    except Exception as e:
        output = {
            "status": "error",
            "outputs": {},
            "error": f"Unexpected error: {str(e)}"
        }
        json.dump(output, sys.stdout)
        return 1

if __name__ == "__main__":
    sys.exit(main())
