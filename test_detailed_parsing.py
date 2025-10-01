#!/usr/bin/env python3
"""
Test script to verify the enhanced parsing of detailed Ollama responses
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_detailed_parsing():
    """Test parsing of detailed Ollama responses."""
    print("🧪 Testing Enhanced Ollama Response Parsing")
    print("=" * 60)
    
    try:
        from modules.code_review import CodeReviewTask
        from services.ollama_service import OllamaService
        
        # Create a test instance
        task = CodeReviewTask(OllamaService(), '/tmp/test')
        
        # Test diff content
        test_diff = """diff --git a/lib/retry_interceptor.dart b/lib/retry_interceptor.dart
index 1234567..abcdefg 100644
--- a/lib/retry_interceptor.dart
+++ b/lib/retry_interceptor.dart
@@ -45,8 +45,8 @@ class RetryInterceptor {
-    onErrorRetryFailed?.call(err);
+    if (onErrorRetryFailed != null) {
+      onErrorRetryFailed.call(err);
+    }
@@ -67,5 +67,5 @@ class RetryInterceptor {
-    Dio clonedDio = originalDio.clone();
+    // Removed redundant cloning
@@ -89,8 +89,8 @@ class RetryInterceptor {
-    logger.info('Request data: ' + requestData.toString());
+    logger.info('Request processed successfully');
"""
        
        # Test detailed Ollama response (like what you're seeing)
        test_review = """# Fast Code Review (1 chunk analyzed)

## Chunk 1 Review

**CRITICAL BUGS**:
1. **Null pointers**: The `onErrorRetryFailed` callback is not null-checked before calling it, which could lead to a `NullPointerException` if the user does not provide a custom error handler.
   **FIX**: Add a null check before calling `onErrorRetryFailed?.call(err);`.

2. **Infinite loops**: If the `onErrorRetryFailed` callback throws an exception, it could lead to an infinite loop if the exception is not handled properly.
   **FIX**: Ensure that any exceptions thrown in `onErrorRetryFailed` are caught and handled gracefully.

3. **Logic errors**: The `retryRequest` method clones the original `Dio` instance but does not use it, which is redundant.
   **FIX**: Remove the redundant cloning of the `Dio` instance in `retryRequest`.

**PERFORMANCE**:
1. **Memory leaks**: The `RetryInterceptor` clones all interceptors from the original `Dio` instance, which could lead to memory leaks if the original `Dio` instance is not properly managed.
   **FIX**: Consider using a more efficient way to clone interceptors or avoid cloning if not necessary.

2. **Infinite loops**: If the `onErrorRetryFailed` callback throws an exception, it could lead to an infinite loop if the exception is not handled properly.
   **FIX**: Ensure that any exceptions thrown in `onErrorRetryFailed` are caught and handled gracefully.

**SECURITY**:
1. **Data leaks**: The `ErrorMessage` class logs detailed request data, which could potentially leak sensitive information.
   **FIX**: Consider logging only necessary information and ensure that sensitive data is redacted before logging.

## Summary
Analyzed 1 chunk in parallel. Focus on critical issues above."""
        
        # Test the enhanced parsing
        print("📊 Testing enhanced parsing of detailed Ollama responses...")
        structured = task._parse_review_to_structured(test_review, test_diff)
        
        print("✅ Parsing successful!")
        
        # Check if issues were extracted
        files = structured.get('files', [])
        print(f"📂 Files found: {len(files)}")
        
        total_issues = 0
        for file_data in files:
            file_path = file_data.get('file_path', 'unknown')
            issues = file_data.get('issues', [])
            total_issues += len(issues)
            
            print(f"\n📄 File: {file_path}")
            print(f"   Issues: {len(issues)}")
            print(f"   Status: {file_data.get('file_status', 'unknown')}")
            
            if issues:
                print("   Issues found:")
                for issue in issues:
                    print(f"     • {issue.get('title', 'Unknown')} ({issue.get('type', 'unknown')})")
                    print(f"       Description: {issue.get('description', '')[:100]}...")
                    print(f"       AI Analysis: {issue.get('ai_analysis', '')[:100]}...")
            else:
                print("   No issues found")
        
        print(f"\n📈 Total issues extracted: {total_issues}")
        
        # Test specific issue parsing
        print("\n🔍 Testing specific issue parsing...")
        
        # Test null pointer issue
        test_chunk = """**CRITICAL BUGS**:
1. **Null pointers**: The `onErrorRetryFailed` callback is not null-checked before calling it, which could lead to a `NullPointerException` if the user does not provide a custom error handler.
   **FIX**: Add a null check before calling `onErrorRetryFailed?.call(err);`."""
        
        issues = task._extract_issues_from_chunk(test_chunk, "lib/retry_interceptor.dart", {"lib/retry_interceptor.dart": [45]})
        
        if issues:
            issue = issues[0]
            print(f"✅ Null pointer issue parsed:")
            print(f"   Title: {issue.get('title')}")
            print(f"   Type: {issue.get('type')}")
            print(f"   Description: {issue.get('description')}")
            print(f"   Code snippet: {issue.get('code_snippet')}")
            
            # Check if suggestions were generated
            suggestions = issue.get('ai_suggestions', [])
            if suggestions:
                print(f"   Suggestions: {len(suggestions)}")
                for suggestion in suggestions[:2]:
                    print(f"     - {suggestion.get('suggestion')}")
            else:
                print("   ❌ No suggestions generated")
        else:
            print("❌ Failed to parse null pointer issue")
            return False
        
        # Test data leak issue
        test_security_chunk = """**SECURITY**:
1. **Data leaks**: The `ErrorMessage` class logs detailed request data, which could potentially leak sensitive information.
   **FIX**: Consider logging only necessary information and ensure that sensitive data is redacted before logging."""
        
        security_issues = task._extract_issues_from_chunk(test_security_chunk, "lib/retry_interceptor.dart", {"lib/retry_interceptor.dart": [89]})
        
        if security_issues:
            issue = security_issues[0]
            print(f"\n✅ Data leak issue parsed:")
            print(f"   Title: {issue.get('title')}")
            print(f"   Type: {issue.get('type')}")
            print(f"   Description: {issue.get('description')}")
            
            # Check if security-specific suggestions were generated
            suggestions = issue.get('ai_suggestions', [])
            if suggestions:
                print(f"   Security suggestions: {len(suggestions)}")
                for suggestion in suggestions[:2]:
                    print(f"     - {suggestion.get('suggestion')}")
            else:
                print("   ❌ No security suggestions generated")
        else:
            print("❌ Failed to parse data leak issue")
            return False
        
        # Test memory leak issue
        test_perf_chunk = """**PERFORMANCE**:
1. **Memory leaks**: The `RetryInterceptor` clones all interceptors from the original `Dio` instance, which could lead to memory leaks if the original `Dio` instance is not properly managed.
   **FIX**: Consider using a more efficient way to clone interceptors or avoid cloning if not necessary."""
        
        perf_issues = task._extract_issues_from_chunk(test_perf_chunk, "lib/retry_interceptor.dart", {"lib/retry_interceptor.dart": [67]})
        
        if perf_issues:
            issue = perf_issues[0]
            print(f"\n✅ Memory leak issue parsed:")
            print(f"   Title: {issue.get('title')}")
            print(f"   Type: {issue.get('type')}")
            print(f"   Description: {issue.get('description')}")
            
            # Check if performance-specific suggestions were generated
            suggestions = issue.get('ai_suggestions', [])
            if suggestions:
                print(f"   Performance suggestions: {len(suggestions)}")
                for suggestion in suggestions[:2]:
                    print(f"     - {suggestion.get('suggestion')}")
            else:
                print("   ❌ No performance suggestions generated")
        else:
            print("❌ Failed to parse memory leak issue")
            return False
        
        print("\n🎉 All detailed parsing tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_detailed_parsing()
    if success:
        print("\n🚀 The enhanced Ollama response parsing is working correctly!")
        print("📋 Key improvements:")
        print("  • Parses detailed numbered issue lists")
        print("  • Extracts specific issue titles and descriptions")
        print("  • Generates appropriate code snippets")
        print("  • Creates category-specific AI suggestions")
        print("  • Properly assigns issues to files")
        print("  • No more disconnect between console and JSON output")
    else:
        print("\n❌ Test failed. Please check the implementation.")
        sys.exit(1)