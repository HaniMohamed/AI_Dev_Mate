#!/usr/bin/env python3
"""
Test script for the new refactored code review format
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_new_format():
    """Test the new JSON format generation."""
    print("🧪 Testing New Code Review Format")
    print("=" * 50)
    
    try:
        from modules.code_review import CodeReviewTask
        from services.ollama_service import OllamaService
        
        # Create a test instance
        task = CodeReviewTask(OllamaService(), '/tmp/test')
        
        # Test diff content
        test_diff = """diff --git a/src/auth/login.py b/src/auth/login.py
index 1234567..abcdefg 100644
--- a/src/auth/login.py
+++ b/src/auth/login.py
@@ -42,8 +42,8 @@ def authenticate_user(username, password):
-    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    query = "SELECT * FROM users WHERE username = ? AND password = ?"
+    cursor.execute(query, (username, password))
@@ -50,5 +50,5 @@ def authenticate_user(username, password):
-    user_role = user.role.name
+    user_role = user.role.name if user and user.role else 'guest'
"""
        
        # Test review content
        test_review = """# Fast Code Review (1 chunk analyzed)

## Chunk 1 Review

1. **SECURITY**: SQL injection, XSS, auth bypass, data leaks
        * ISSUE: The code contains vulnerabilities that can be exploited for malicious purposes, such as SQL injection, cross-site scripting (XSS), and authentication bypass.
        * FIX: Implement proper sanitization and validation measures for user input, use prepared statements, and ensure that sensitive data is properly encrypted.
2. **CRITICAL BUGS**: Null pointers, crashes, logic errors
        * ISSUE: The code contains critical bugs that can cause the application to crash or produce incorrect results.
        * FIX: Ensure that all variables are properly initialized, use defensive programming techniques, and test the code thoroughly to catch any logic errors.

## Summary
Analyzed 1 chunk in parallel. Focus on critical issues above."""
        
        # Test the new parsing
        print("📊 Testing new structured parsing...")
        structured = task._parse_review_to_structured(test_review, test_diff)
        
        print("✅ Parsing successful!")
        print(f"📁 Files analyzed: {structured['review_metadata']['total_files_analyzed']}")
        print(f"📈 Total issues: {structured['review_metadata']['total_issues_found']}")
        print(f"🔒 Security issues: {structured['summary']['security_issues']}")
        print(f"🐛 Critical bugs: {structured['summary']['critical_issues']}")
        
        # Test file structure
        files = structured.get('files', [])
        print(f"📂 Files in structure: {len(files)}")
        
        for file_data in files:
            if file_data.get('total_issues', 0) > 0:
                print(f"  📄 {file_data['file_path']} ({file_data['total_issues']} issues)")
                for issue in file_data.get('issues', [])[:2]:
                    print(f"    • {issue['title']} (Line {issue.get('line_number', 'N/A')})")
                    print(f"      Severity: {issue['severity']}")
                    print(f"      Fix time: {issue['estimated_fix_time']}")
        
        # Test recommendations
        recommendations = structured.get('recommendations', {})
        immediate_actions = recommendations.get('immediate_actions', [])
        print(f"🚨 Immediate actions: {len(immediate_actions)}")
        
        # Test next steps
        next_steps = structured.get('next_steps', [])
        print(f"🎯 Next steps: {len(next_steps)}")
        
        # Save sample output
        with open('test_new_format_output.json', 'w') as f:
            json.dump(structured, f, indent=2)
        
        print("📄 Sample output saved to test_new_format_output.json")
        
        # Validate structure
        required_keys = ['review_metadata', 'summary', 'files', 'recommendations', 'next_steps']
        for key in required_keys:
            if key not in structured:
                print(f"❌ Missing required key: {key}")
                return False
        
        print("✅ All required keys present!")
        
        # Test issue structure
        if files:
            file_with_issues = next((f for f in files if f.get('total_issues', 0) > 0), None)
            if file_with_issues:
                issue = file_with_issues['issues'][0]
                required_issue_keys = ['id', 'type', 'severity', 'title', 'description', 'line_number', 'ai_suggestions']
                for key in required_issue_keys:
                    if key not in issue:
                        print(f"❌ Missing issue key: {key}")
                        return False
        
        print("✅ Issue structure valid!")
        print("🎉 New format test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_new_format()
    if success:
        print("\n🚀 The refactored code review system is working correctly!")
        print("📋 Key improvements:")
        print("  • File-organized issues")
        print("  • Specific line numbers")
        print("  • Detailed AI suggestions")
        print("  • Priority-based recommendations")
        print("  • Time estimates for fixes")
        print("  • Much more readable JSON output")
    else:
        print("\n❌ Test failed. Please check the implementation.")
        sys.exit(1)