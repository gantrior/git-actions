#!/usr/bin/env python3
"""Confluence comment action script.

This script posts a comment to a Confluence page.
Input: JSON with page ID and comment text
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
        page_id = inputs.get("pageId")
        comment = inputs.get("comment")
        
        # Validate required inputs
        if not page_id or not comment:
            output = {
                "status": "error",
                "outputs": {},
                "error": "Missing required inputs: pageId and comment"
            }
            json.dump(output, sys.stdout)
            return 1
        
        # In a real implementation, this would call the Confluence API
        # For now, we'll simulate a successful comment post
        
        confluence_url = os.environ.get("CONFLUENCE_URL", "https://confluence.example.com")
        
        # Simulate successful API call
        comment_id = "98765"
        comment_url = f"{confluence_url}/pages/viewpage.action?pageId={page_id}#comment-{comment_id}"
        
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
