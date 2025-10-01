#!/usr/bin/env python3
"""
Test script to verify the file analysis fix
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_file_analysis_fix():
    """Test that file analysis generates real, specific analysis."""
    print("🧪 Testing File Analysis Fix")
    print("=" * 50)
    
    try:
        from modules.code_review import CodeReviewTask
        from services.ollama_service import OllamaService
        
        # Create a test instance
        task = CodeReviewTask(OllamaService(), '/tmp/test')
        
        # Test diff content with multiple files
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

diff --git a/src/database/queries.py b/src/database/queries.py
index 1234567..abcdefg 100644
--- a/src/database/queries.py
+++ b/src/database/queries.py
@@ -23,8 +23,8 @@ def get_user_data(user_id):
-    return f"<div>Welcome {user_input}</div>"
+    return f"<div>Welcome {html.escape(user_input)}</div>"

diff --git a/src/utils/helpers.py b/src/utils/helpers.py
index 1234567..abcdefg 100644
--- a/src/utils/helpers.py
+++ b/src/utils/helpers.py
@@ -10,5 +10,5 @@ def format_date(date):
-    # Basic date formatting
+    # Improved date formatting with timezone support
     return date.strftime('%Y-%m-%d')
"""
        
        # Test review content with issues for different files
        test_review = """# Fast Code Review (3 chunks analyzed)

## Chunk 1 Review

1. **SECURITY**: SQL injection, XSS, auth bypass, data leaks
        * ISSUE: The code contains vulnerabilities that can be exploited for malicious purposes, such as SQL injection, cross-site scripting (XSS), and authentication bypass.
        * FIX: Implement proper sanitization and validation measures for user input, use prepared statements, and ensure that sensitive data is properly encrypted.

## Chunk 2 Review

1. **SECURITY**: XSS vulnerability in user output
        * ISSUE: User input is directly inserted into HTML without proper escaping, allowing potential XSS attacks.
        * FIX: Escape all user-generated content before displaying it in HTML.

## Chunk 3 Review

1. **CODE QUALITY**: Basic implementation without error handling
        * ISSUE: The code lacks proper error handling and could benefit from more robust implementation.
        * FIX: Add comprehensive error handling and improve code structure.

## Summary
Analyzed 3 chunks in parallel. Focus on critical issues above."""
        
        # Test the new parsing
        print("📊 Testing file analysis generation...")
        structured = task._parse_review_to_structured(test_review, test_diff)
        
        print("✅ Parsing successful!")
        
        # Check files structure
        files = structured.get('files', [])
        print(f"📂 Files found: {len(files)}")
        
        # Test file analysis generation
        for file_data in files:
            file_path = file_data.get('file_path', 'unknown')
            total_issues = file_data.get('total_issues', 0)
            ai_analysis = file_data.get('ai_analysis', '')
            
            print(f"\n📄 File: {file_path}")
            print(f"   Issues: {total_issues}")
            print(f"   Analysis: {ai_analysis[:100]}...")
            
            # Check if analysis is generic
            if "This file follows good practices with proper error handling, input validation, and secure coding patterns." in ai_analysis:
                if total_issues > 0:
                    print("❌ ERROR: File with issues has generic analysis!")
                    return False
                else:
                    print("✅ OK: Clean file has appropriate analysis")
            else:
                print("✅ OK: File has specific analysis")
        
        # Test the file analysis generation method directly
        print("\n🔍 Testing _generate_file_analysis method...")
        
        # Test with security issues
        security_issues = [
            {
                "id": "SEC-001",
                "type": "security",
                "description": "SQL injection vulnerability",
                "title": "SQL Injection Vulnerability"
            }
        ]
        
        analysis = task._generate_file_analysis("src/auth/login.py", security_issues)
        print(f"Security analysis: {analysis}")
        
        if "SQL injection" in analysis and "security issue" in analysis:
            print("✅ Security analysis is specific and accurate")
        else:
            print("❌ Security analysis is not specific enough")
            return False
        
        # Test with multiple issue types
        mixed_issues = [
            {
                "id": "SEC-001",
                "type": "security",
                "description": "SQL injection vulnerability",
                "title": "SQL Injection Vulnerability"
            },
            {
                "id": "BUG-001",
                "type": "critical_bug",
                "description": "null pointer exception",
                "title": "Null Pointer Exception"
            }
        ]
        
        mixed_analysis = task._generate_file_analysis("src/auth/login.py", mixed_issues)
        print(f"Mixed analysis: {mixed_analysis}")
        
        if "security issue" in mixed_analysis and "critical bug" in mixed_analysis:
            print("✅ Mixed analysis covers all issue types")
        else:
            print("❌ Mixed analysis is incomplete")
            return False
        
        # Test clean file analysis
        clean_analysis = task._generate_clean_file_analysis("src/utils/helpers.py")
        print(f"Clean analysis: {clean_analysis}")
        
        if "utility file" in clean_analysis.lower():
            print("✅ Clean analysis is file-type specific")
        else:
            print("❌ Clean analysis is not file-type specific")
            return False
        
        print("\n🎉 All file analysis tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_file_analysis_fix()
    if success:
        print("\n🚀 The file analysis fix is working correctly!")
        print("📋 Key improvements:")
        print("  • Real AI analysis based on actual issues")
        print("  • File-type specific analysis for clean files")
        print("  • Proper issue distribution to files")
        print("  • No more generic messages for files with issues")
    else:
        print("\n❌ Test failed. Please check the implementation.")
        sys.exit(1)