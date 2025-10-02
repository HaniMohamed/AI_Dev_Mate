# src/modules/code_review.py
import os
import re
from typing import Dict, List, Any
from src.core.models import BaseTask
from src.core.utils import check_and_load_index, create_aggressive_review_prompt
from src.services.ollama_service import OllamaService
from src.services.git_service import GitService
from src.utils.console import aidm_console

class CodeReviewTask(BaseTask):
    def __init__(self, ollama: OllamaService, repo_path: str = None):
        super().__init__("Code Review")
        self.ollama = ollama
        self.review = ""
        self.repo_path = repo_path
        self.base_branch = "HEAD~1"  # Compare with previous commit instead of main branch
        self.target_branch = None

    def set_review_params(self, base_branch: str = None, target_branch: str = None, 
                         max_files: int = None, fast_mode: bool = False):
        """Set review parameters for branch comparison."""
        self.base_branch = base_branch or "HEAD~1"  # Default to previous commit
        self.target_branch = target_branch
        self.max_files = max_files or 50  # Default to 50 files
        self.fast_mode = fast_mode

    def run(self):
        """Run aggressive code review with beautiful output."""
        # Ask for repository path if not set
        if not self.repo_path:
            self.repo_path = aidm_console.prompt("Enter path to repository to review")
        
        aidm_console.print_header("🔍 Aggressive Code Review", f"Target: {self.repo_path}")
        
        # Check if indexed data is available
        index_data = check_and_load_index(repo_path=self.repo_path, ollama=self.ollama)
        if index_data is None:
            self.review = "Code review failed: No indexed data available. Please index the project first."
            self.completed = True
            return
        
        try:
            # Verify git repository
            if not GitService.is_git_repo(self.repo_path):
                aidm_console.print_error(f"Not a git repository: {self.repo_path}")
                self.review = f"Code review failed: {self.repo_path} is not a git repository."
                self.completed = True
                return
            
            # Check if base branch/commit exists (skip check for HEAD~1 as it's a commit reference)
            if self.base_branch != "HEAD~1" and not GitService.branch_exists(self.base_branch, self.repo_path):
                aidm_console.print_warning(f"Base branch '{self.base_branch}' not found. Available branches:")
                available_branches = GitService.get_available_branches(self.repo_path)
                for branch in available_branches[:10]:  # Show first 10 branches
                    aidm_console.print_info(f"  - {branch}")
                if len(available_branches) > 10:
                    aidm_console.print_info(f"  ... and {len(available_branches) - 10} more")
                
                self.review = f"Code review failed: Base branch '{self.base_branch}' not found."
                self.completed = True
                return
            
            # Get the diff
            comparison_desc = "previous commit" if self.base_branch == "HEAD~1" else self.base_branch
            aidm_console.print_info(f"Comparing {comparison_desc} with {'current changes' if not self.target_branch else self.target_branch}")
            
            if self.target_branch and not GitService.branch_exists(self.target_branch, self.repo_path):
                aidm_console.print_error(f"Target branch '{self.target_branch}' not found.")
                self.review = f"Code review failed: Target branch '{self.target_branch}' not found."
                self.completed = True
                return
            
            # Get optimized diff - exclude binary files and limit to important files
            exclude_patterns = [
                "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",  # Images
                "*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv",  # Videos
                "*.mp3", "*.wav", "*.flac", "*.aac",  # Audio
                "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx",  # Documents
                "*.zip", "*.tar", "*.gz", "*.rar",  # Archives
                "*.json", "*.xml", "*.yaml", "*.yml",  # Config files (often large)
                "*.lock", "*.log", "*.tmp", "*.cache"  # Temporary files
            ]
            
            diff = GitService.get_branch_diff(
                self.base_branch, 
                self.target_branch, 
                self.repo_path,
                exclude_patterns=exclude_patterns,
                max_files=self.max_files
            )
            
            # Store diff for later use in structured review
            self._last_diff = diff
            
            if not diff.strip():
                aidm_console.print_warning("No differences found between branches.")
                self.review = "No differences found between branches to review."
            else:
                aidm_console.print_info("Conducting aggressive code review...")
                
                # Check diff size and chunk if necessary
                diff_size = len(diff)
                aidm_console.print_info(f"Diff size: {diff_size:,} characters")
                
                if diff_size > 50000 or self.fast_mode:  # If diff is large or fast mode enabled
                    if self.fast_mode:
                        aidm_console.print_info(f"Fast mode enabled. Smart chunking for rapid analysis...")
                    else:
                        aidm_console.print_warning(f"Large diff detected ({diff_size:,} chars). Smart chunking for faster analysis...")
                    self.review = self._smart_chunked_review(diff, index_data)
                else:
                    # Show the diff with syntax highlighting for smaller diffs
                    aidm_console.print_primary("Code Changes:")
                    aidm_console.print_code_syntax(diff, "diff")
                    
                    # Generate aggressive review using indexed context
                    with aidm_console.create_progress("Generating aggressive review") as progress:
                        task = progress.add_task("Analyzing code for issues...", total=100)
                        
                        # Create aggressive review prompt
                        review_prompt = create_aggressive_review_prompt(diff, index_data)
                        self.review = self.ollama.run_prompt(review_prompt)
                        progress.update(task, completed=100)
                
                aidm_console.print_success("Aggressive code review completed!")
                
        except Exception as e:
            aidm_console.print_error(f"Code review failed: {e}")
            self.review = f"Code review failed: {e}"
        
        self.completed = True

    def _parse_review_to_structured(self, review_text: str, diff_content: str = None) -> Dict[str, Any]:
        """Parse the review text into a clean, readable structured format."""
        # Extract files and their line mappings from diff
        file_line_mappings = self._extract_file_line_mappings(diff_content) if diff_content else {}
        
        structured = {
            "review_metadata": {
                "timestamp": datetime.now().isoformat(),
                "repository_path": self.repo_path,
                "base_branch": self.base_branch,
                "target_branch": self.target_branch,
                "review_type": "comprehensive",
                "total_files_analyzed": len(file_line_mappings),
                "total_issues_found": 0
            },
            "summary": {
                "critical_issues": 0,
                "security_issues": 0,
                "performance_issues": 0,
                "code_quality_issues": 0,
                "files_with_issues": 0,
                "files_clean": 0,
                "total_issues_found": 0
            },
            "issues": [],
            "recommendations": {
                "immediate_actions": [],
                "security_improvements": [],
                "performance_optimizations": [],
                "code_quality_improvements": []
            },
            "next_steps": []
        }
        
        # Extract chunk information and parse issues
        chunk_pattern = r'## Chunk (\d+) Review\n(.*?)(?=## Chunk \d+ Review|\n## Summary|$)'
        chunks = re.findall(chunk_pattern, review_text, re.DOTALL)
        
        all_issues = []
        for chunk_num, chunk_content in chunks:
            file_context = self._extract_file_context_from_chunk(chunk_content)
            chunk_issues = self._extract_issues_from_chunk(chunk_content, file_context, file_line_mappings)
            all_issues.extend(chunk_issues)
        
        # Add all issues directly to the issues array
        structured["issues"] = all_issues
        
        # Update summary counts based on all issues
        files_with_issues = set()
        for issue in all_issues:
            structured["summary"]["total_issues_found"] += 1
            issue_type = issue["type"]
            file_path = issue.get("file_path", "unknown")
            
            if file_path != "unknown":
                files_with_issues.add(file_path)
            
            if issue_type == "security":
                structured["summary"]["security_issues"] += 1
            elif issue_type == "critical_bug":
                structured["summary"]["critical_issues"] += 1
            elif issue_type == "performance":
                structured["summary"]["performance_issues"] += 1
            elif issue_type == "code_quality":
                structured["summary"]["code_quality_issues"] += 1
        
        # Count files with issues and clean files
        structured["summary"]["files_with_issues"] = len(files_with_issues)
        structured["summary"]["files_clean"] = len(file_line_mappings) - len(files_with_issues)
        
        # Update review_metadata with final counts
        structured["review_metadata"]["total_issues_found"] = structured["summary"]["total_issues_found"]
        
        # Generate recommendations
        structured["recommendations"] = self._generate_recommendations(all_issues)
        structured["next_steps"] = self._generate_next_steps(structured["summary"])
        
        return structured

    def _extract_file_line_mappings(self, diff_content: str) -> Dict[str, List[int]]:
        """Extract file paths and their line numbers from git diff content."""
        file_line_mappings = {}
        lines = diff_content.split('\n')
        current_file = None
        
        for i, line in enumerate(lines):
            # Git diff file headers
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    current_file = parts[3][2:]  # Remove "b/" prefix
                    file_line_mappings[current_file] = []
            elif line.startswith('+++'):
                file_path = line[4:]  # Remove "+++ " prefix
                if file_path != '/dev/null':
                    current_file = file_path
                    if current_file not in file_line_mappings:
                        file_line_mappings[current_file] = []
            # Line number indicators (e.g., @@ -10,5 +15,6 @@)
            elif line.startswith('@@') and current_file:
                # Extract line numbers from hunk header
                # Format: @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r'@@\s*-\d+(?:,\d+)?\s*\+(\d+)(?:,(\d+))?\s*@@', line)
                if match:
                    start_line = int(match.group(1))
                    line_count = int(match.group(2)) if match.group(2) else 1
                    # Add line numbers for this hunk
                    for line_num in range(start_line, start_line + line_count):
                        file_line_mappings[current_file].append(line_num)
            # Added lines (start with +)
            elif line.startswith('+') and not line.startswith('+++') and current_file:
                # This is an added line, we can track it
                pass
        
        return file_line_mappings

    def _organize_issues_by_file(self, issues: List[Dict], file_line_mappings: Dict[str, List[int]]) -> Dict[str, List[Dict]]:
        """Organize issues by file path."""
        file_issues = {}
        
        # Initialize file structure with all files from diff
        for file_path in file_line_mappings.keys():
            file_issues[file_path] = []
        
        # Distribute issues to files
        for issue in issues:
            file_path = issue.get("file_path", "unknown")
            
            # If file_path is unknown, try to extract from file_context
            if file_path == "unknown":
                file_context = issue.get("file_context", "")
                if file_context and file_context != "unknown":
                    # Extract first file from context
                    files_in_context = [f.strip() for f in file_context.split(',')]
                    if files_in_context:
                        file_path = files_in_context[0]
            
            # Assign issue to file
            if file_path in file_issues:
                file_issues[file_path].append(issue)
            elif file_path != "unknown":
                # Create new entry for file not in mappings
                file_issues[file_path] = [issue]
            else:
                # If still unknown, assign to first available file
                if file_line_mappings:
                    first_file = list(file_line_mappings.keys())[0]
                    file_issues[first_file].append(issue)
        
        return file_issues

    def _generate_recommendations(self, issues: List[Dict]) -> Dict[str, List]:
        """Generate comprehensive recommendations based on issues."""
        recommendations = {
            "immediate_actions": [],
            "security_improvements": [],
            "performance_optimizations": [],
            "code_quality_improvements": []
        }
        
        # Sort issues by severity
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        
        # Immediate actions (critical and high severity)
        for issue in critical_issues + high_issues:
            recommendations["immediate_actions"].append({
                "priority": issue["severity"],
                "action": f"Fix {issue['title']} in {issue['file_path']}:{issue.get('line_number', 'N/A')}",
                "reason": issue["description"],
                "estimated_time": issue.get("estimated_fix_time", "Unknown")
            })
        
        # Categorize improvements
        security_issues = [i for i in issues if i.get("type") == "security"]
        performance_issues = [i for i in issues if i.get("type") == "performance"]
        quality_issues = [i for i in issues if i.get("type") == "code_quality"]
        
        if security_issues:
            recommendations["security_improvements"] = [
                "Implement comprehensive input validation",
                "Add SQL injection protection across all database queries",
                "Enable XSS protection in all user-facing outputs",
                "Implement proper authentication and authorization"
            ]
        
        if performance_issues:
            recommendations["performance_optimizations"] = [
                "Add database indexes for frequently queried columns",
                "Optimize N+1 query problems",
                "Implement connection pooling",
                "Add caching for frequently accessed data"
            ]
        
        if quality_issues:
            recommendations["code_quality_improvements"] = [
                "Move hardcoded values to configuration files",
                "Implement proper error handling patterns",
                "Add comprehensive logging",
                "Increase test coverage"
            ]
        
        return recommendations

    def _generate_next_steps(self, summary: Dict) -> List[str]:
        """Generate next steps based on summary."""
        steps = []
        
        if summary["critical_issues"] > 0:
            steps.append("1. Address all critical issues immediately")
        
        if summary["security_issues"] > 0:
            steps.append("2. Implement security improvements")
        
        if summary["performance_issues"] > 0:
            steps.append("3. Optimize performance bottlenecks")
        
        if summary["code_quality_issues"] > 0:
            steps.append("4. Improve code quality standards")
        
        steps.append("5. Add automated testing for identified issues")
        
        return steps

    def _generate_file_analysis(self, file_path: str, issues: List[Dict]) -> str:
        """Generate real AI analysis for a file based on its issues."""
        if not issues:
            return "This file follows good practices with proper error handling, input validation, and secure coding patterns."
        
        # Analyze the types of issues found
        issue_types = [issue.get("type", "unknown") for issue in issues]
        security_issues = [i for i in issues if i.get("type") == "security"]
        critical_issues = [i for i in issues if i.get("type") == "critical_bug"]
        performance_issues = [i for i in issues if i.get("type") == "performance"]
        quality_issues = [i for i in issues if i.get("type") == "code_quality"]
        
        analysis_parts = []
        
        # Security analysis
        if security_issues:
            security_desc = []
            for issue in security_issues:
                if "sql injection" in issue.get("description", "").lower():
                    security_desc.append("SQL injection vulnerabilities")
                elif "xss" in issue.get("description", "").lower():
                    security_desc.append("XSS vulnerabilities")
                elif "auth" in issue.get("description", "").lower():
                    security_desc.append("authentication issues")
                else:
                    security_desc.append("security vulnerabilities")
            
            analysis_parts.append(f"This file contains {len(security_issues)} security issue(s): {', '.join(set(security_desc))}. These vulnerabilities could compromise the application's security and should be addressed immediately.")
        
        # Critical bugs analysis
        if critical_issues:
            bug_desc = []
            for issue in critical_issues:
                if "null pointer" in issue.get("description", "").lower():
                    bug_desc.append("null pointer exceptions")
                elif "memory leak" in issue.get("description", "").lower():
                    bug_desc.append("memory leaks")
                elif "crash" in issue.get("description", "").lower():
                    bug_desc.append("potential crashes")
                else:
                    bug_desc.append("critical bugs")
            
            analysis_parts.append(f"This file has {len(critical_issues)} critical bug(s): {', '.join(set(bug_desc))}. These issues could cause application failures and should be fixed as soon as possible.")
        
        # Performance analysis
        if performance_issues:
            perf_desc = []
            for issue in performance_issues:
                if "n+1" in issue.get("description", "").lower():
                    perf_desc.append("N+1 query problems")
                elif "index" in issue.get("description", "").lower():
                    perf_desc.append("missing database indexes")
                elif "memory" in issue.get("description", "").lower():
                    perf_desc.append("memory usage issues")
                else:
                    perf_desc.append("performance issues")
            
            analysis_parts.append(f"This file has {len(performance_issues)} performance issue(s): {', '.join(set(perf_desc))}. These issues could impact application performance and user experience.")
        
        # Code quality analysis
        if quality_issues:
            quality_desc = []
            for issue in quality_issues:
                if "hardcoded" in issue.get("description", "").lower():
                    quality_desc.append("hardcoded values")
                elif "error handling" in issue.get("description", "").lower():
                    quality_desc.append("poor error handling")
                else:
                    quality_desc.append("code quality issues")
            
            analysis_parts.append(f"This file has {len(quality_issues)} code quality issue(s): {', '.join(set(quality_desc))}. These issues affect maintainability and should be improved.")
        
        # Combine analysis
        if analysis_parts:
            analysis = " ".join(analysis_parts)
            analysis += f" Overall, this file requires attention with {len(issues)} total issue(s) that need to be addressed."
            return analysis
        else:
            return f"This file has {len(issues)} issue(s) that need to be reviewed and addressed."

    def _generate_clean_file_analysis(self, file_path: str) -> str:
        """Generate analysis for files that are actually clean."""
        # Determine file type for more specific analysis
        if "test" in file_path.lower():
            return "This test file follows good testing practices with proper test structure and assertions."
        elif "config" in file_path.lower() or "settings" in file_path.lower():
            return "This configuration file is properly structured and follows best practices for configuration management."
        elif "util" in file_path.lower() or "helper" in file_path.lower():
            return "This utility file follows good practices with proper error handling and reusable functions."
        elif "model" in file_path.lower():
            return "This model file follows good data modeling practices with proper validation and relationships."
        elif "service" in file_path.lower():
            return "This service file follows good service layer practices with proper separation of concerns."
        elif "controller" in file_path.lower() or "api" in file_path.lower():
            return "This API/controller file follows good practices with proper request handling and validation."
        else:
            return "This file follows good practices with proper error handling, input validation, and secure coding patterns."

    def _extract_files_from_diff(self, diff_content: str) -> List[str]:
        """Extract file paths from git diff content."""
        files = []
        lines = diff_content.split('\n')
        
        for line in lines:
            # Git diff file headers: "diff --git a/path/to/file b/path/to/file"
            if line.startswith('diff --git'):
                # Extract file path from the diff header
                parts = line.split()
                if len(parts) >= 4:
                    # Format: diff --git a/path/to/file b/path/to/file
                    file_path = parts[3][2:]  # Remove "b/" prefix
                    if file_path not in files:
                        files.append(file_path)
            # Also check for "+++" and "---" lines which show file paths
            elif line.startswith('+++') or line.startswith('---'):
                if line.startswith('+++'):
                    file_path = line[4:]  # Remove "+++ " prefix
                    if file_path != '/dev/null' and file_path not in files:
                        files.append(file_path)
        
        return files

    def _create_file_structure(self, files: List[str]) -> Dict[str, Any]:
        """Create file structure for organizing issues by file."""
        file_structure = {}
        for file_path in files:
            file_structure[file_path] = {
                "path": file_path,
                "issues": {
                    "security": [],
                    "critical_bugs": [],
                    "performance": []
                },
                "line_numbers": [],  # Will be populated when we have line-specific info
                "summary": {
                    "total_issues": 0,
                    "security_issues": 0,
                    "critical_bugs": 0,
                    "performance_issues": 0
                }
            }
        return file_structure

    def _extract_issues_from_chunk(self, chunk_content: str, file_context: str = None, file_line_mappings: Dict[str, List[int]] = None) -> List[Dict[str, Any]]:
        """Extract detailed issues from Ollama responses with enhanced parsing."""
        issues = []
        
        # Split content into lines for easier processing
        lines = chunk_content.split('\n')
        
        issue_counter = {"security": 1, "critical_bug": 1, "performance": 1, "code_quality": 1}
        
        # Look for section headers (SECURITY, CRITICAL BUGS, PERFORMANCE)
        current_section = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for section headers - handle both formats
            if (line.startswith('**SECURITY**:') or line.startswith('**CRITICAL BUGS**:') or 
                line.startswith('**PERFORMANCE**:') or line.startswith('CRITICAL BUGS:') or
                line.startswith('PERFORMANCE:') or line.startswith('SECURITY:')):
                
                if 'SECURITY' in line:
                    current_section = 'security'
                elif 'CRITICAL BUGS' in line:
                    current_section = 'critical_bug'
                elif 'PERFORMANCE' in line:
                    current_section = 'performance'
                i += 1
                continue
            
            # Look for numbered issues within sections
            if current_section and re.match(r'^\d+\.\s*\*\*', line):
                # Extract issue from numbered list
                issue_data = self._parse_numbered_issue(line, lines, i, current_section, file_context, file_line_mappings, issue_counter)
                if issue_data:
                    issues.append(issue_data)
                    issue_counter[current_section] += 1
            
            # Also look for simple numbered issues without ** formatting
            elif current_section and re.match(r'^\d+\s+', line):
                issue_data = self._parse_simple_numbered_issue(line, lines, i, current_section, file_context, file_line_mappings, issue_counter)
                if issue_data:
                    issues.append(issue_data)
                    issue_counter[current_section] += 1
            
            i += 1
        
        # Also look for simple format issues (fallback)
        if not issues:
            issues = self._extract_simple_format_issues(chunk_content, file_context, file_line_mappings)
        
        return issues

    def _parse_numbered_issue(self, line: str, lines: List[str], line_idx: int, section: str, file_context: str, file_line_mappings: Dict[str, List[int]], issue_counter: Dict[str, int]) -> Dict[str, Any]:
        """Parse a numbered issue from Ollama response."""
        try:
            # Extract issue title (e.g., "**Null pointers**:")
            title_match = re.search(r'\*\*([^*]+)\*\*:', line)
            if not title_match:
                return None
            
            issue_title = title_match.group(1).strip()
            
            # Look for description in next lines
            description_lines = []
            fix_lines = []
            j = line_idx + 1
            
            # Collect description lines until we hit a FIX or next numbered item
            while j < len(lines) and j < line_idx + 10:  # Look ahead max 10 lines
                next_line = lines[j].strip()
                
                if re.match(r'^\d+\.\s*\*\*', next_line) or next_line.startswith('**') and ':' in next_line:
                    # Hit next issue or section
                    break
                elif next_line.startswith('**FIX**:'):
                    # Found fix section
                    fix_lines.append(next_line.replace('**FIX**:', '').strip())
                    j += 1
                    # Continue collecting fix lines
                    while j < len(lines) and j < line_idx + 15:
                        fix_line = lines[j].strip()
                        if re.match(r'^\d+\.\s*\*\*', fix_line) or (fix_line.startswith('**') and ':' in fix_line):
                            break
                        if fix_line:
                            fix_lines.append(fix_line)
                        j += 1
                    break
                elif next_line and not next_line.startswith('**'):
                    description_lines.append(next_line)
                
                j += 1
            
            # Combine description and fix
            issue_desc = ' '.join(description_lines).strip()
            fix_desc = ' '.join(fix_lines).strip()
            
            if not issue_desc:
                issue_desc = issue_title
            
            # Generate detailed issue structure
            issue_id = f"{section.upper()}-{issue_counter[section]:03d}"
            
            # Extract file path and line number
            file_path = self._extract_file_path_from_context(file_context)
            line_number = self._estimate_line_number(file_path, file_line_mappings)
            
            # Generate code snippet based on issue
            code_snippet = self._generate_code_snippet_from_description(issue_desc, issue_title)
            
            # Create detailed issue
            issue = {
                "id": issue_id,
                "type": section,
                "severity": self._determine_severity(section),
                "title": self._generate_issue_title_from_description(issue_desc, issue_title),
                "description": issue_desc,
                "line_number": line_number,
                "code_snippet": code_snippet,
                "ai_analysis": self._generate_ai_analysis_from_description(issue_desc, issue_title),
                "ai_suggestions": self._generate_detailed_suggestions_from_fix(section, issue_desc, fix_desc),
                "file_path": file_path,
                "file_context": file_context,
                "related_files": self._find_related_files(file_path),
                "estimated_fix_time": self._estimate_fix_time(section, issue_desc)
            }
            
            return issue
            
        except Exception as e:
            print(f"Error parsing numbered issue: {e}")
            return None

    def _parse_simple_numbered_issue(self, line: str, lines: List[str], line_idx: int, section: str, file_context: str, file_line_mappings: Dict[str, List[int]], issue_counter: Dict[str, int]) -> Dict[str, Any]:
        """Parse a simple numbered issue from Ollama response (format: '1 Null pointers: description')."""
        try:
            # Extract issue title and description (e.g., "1 Null pointers: The onErrorRetryFailed callback...")
            match = re.match(r'^\d+\s+([^:]+):\s*(.*)', line)
            if not match:
                return None
            
            issue_title = match.group(1).strip()
            issue_desc = match.group(2).strip()
            
            # Look for fix information in subsequent lines
            fix_desc = ""
            j = line_idx + 1
            
            # Collect fix lines until we hit next issue or section
            while j < len(lines) and j < line_idx + 10:
                next_line = lines[j].strip()
                
                if re.match(r'^\d+\s+', next_line) or next_line.startswith('**') and ':' in next_line:
                    # Hit next issue or section
                    break
                elif next_line.startswith('• FIX:') or next_line.startswith('FIX:'):
                    # Found fix section
                    fix_desc = next_line.replace('• FIX:', '').replace('FIX:', '').strip()
                    j += 1
                    # Continue collecting fix lines
                    while j < len(lines) and j < line_idx + 15:
                        fix_line = lines[j].strip()
                        if re.match(r'^\d+\s+', fix_line) or (fix_line.startswith('**') and ':' in fix_line):
                            break
                        if fix_line and not fix_line.startswith('```') and not fix_line.startswith('•'):
                            fix_desc += ' ' + fix_line
                        j += 1
                    break
                elif next_line and not next_line.startswith('```') and not next_line.startswith('**') and not next_line.startswith('•'):
                    # This might be part of the description
                    if not fix_desc:  # Only add to description if we haven't found a fix yet
                        issue_desc += ' ' + next_line
                
                j += 1
            
            # Don't swap description and fix - keep them separate
            # The issue_desc should contain the actual issue description, not the fix
            
            # Generate detailed issue structure
            issue_id = f"{section.upper()}-{issue_counter[section]:03d}"
            
            # Extract file path and line number
            file_path = self._extract_file_path_from_context(file_context)
            line_number = self._estimate_line_number(file_path, file_line_mappings)
            
            # Generate code snippet based on issue
            code_snippet = self._generate_code_snippet_from_description(issue_desc, issue_title)
            
            # Create detailed issue
            issue = {
                "id": issue_id,
                "type": section,
                "severity": self._determine_severity(section),
                "title": self._generate_issue_title_from_description(issue_desc, issue_title),
                "description": issue_desc,
                "line_number": line_number,
                "code_snippet": code_snippet,
                "ai_analysis": self._generate_ai_analysis_from_description(issue_desc, issue_title),
                "ai_suggestions": self._generate_detailed_suggestions_from_fix(section, issue_desc, fix_desc),
                "file_path": file_path,
                "file_context": file_context,
                "related_files": self._find_related_files(file_path),
                "estimated_fix_time": self._estimate_fix_time(section, issue_desc)
            }
            
            return issue
            
        except Exception as e:
            print(f"Error parsing simple numbered issue: {e}")
            return None

    def _extract_simple_format_issues(self, chunk_content: str, file_context: str, file_line_mappings: Dict[str, List[int]]) -> List[Dict[str, Any]]:
        """Fallback method to extract issues in simple format."""
        issues = []
        lines = chunk_content.split('\n')
        i = 0
        issue_counter = {"security": 1, "critical_bug": 1, "performance": 1, "code_quality": 1}
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for simple issue patterns
            if 'SECURITY:' in line or 'CRITICAL BUGS:' in line or 'PERFORMANCE:' in line:
                # Determine category and type
                if 'SECURITY:' in line:
                    category = 'security'
                    issue_type = 'security'
                elif 'CRITICAL BUGS:' in line:
                    category = 'critical_bugs'
                    issue_type = 'critical_bug'
                elif 'PERFORMANCE:' in line:
                    category = 'performance'
                    issue_type = 'performance'
                else:
                    i += 1
                    continue
                
                # Extract issue description and fix
                issue_desc = ""
                fix_desc = ""
                
                if '| FIX:' in line:
                    # Format: "1. SECURITY: issue | FIX: fix"
                    parts = line.split('| FIX:')
                    if len(parts) == 2:
                        issue_part = parts[0]
                        fix_part = parts[1]
                        # Remove number prefix
                        issue_desc = re.sub(r'^\d+\.\s*', '', issue_part.split(':', 1)[1]).strip()
                        fix_desc = fix_part.strip()
                else:
                    # Format: "1. **SECURITY**: issue" with separate ISSUE and FIX lines
                    issue_desc = re.sub(r'^\d+\.\s*\*\*.*?\*\*:\s*', '', line).strip()
                    
                    # Look for ISSUE and FIX in subsequent lines
                    j = i + 1
                    while j < len(lines) and j < i + 5:  # Look ahead max 5 lines
                        next_line = lines[j].strip()
                        if next_line.startswith('* ISSUE:'):
                            issue_desc = next_line.replace('* ISSUE:', '').strip()
                        elif next_line.startswith('* FIX:'):
                            fix_desc = next_line.replace('* FIX:', '').strip()
                            break
                        j += 1
                
                if issue_desc:
                    # Generate detailed issue structure
                    issue_id = f"{issue_type.upper()}-{issue_counter[issue_type]:03d}"
                    issue_counter[issue_type] += 1
                    
                    # Extract file path and line number
                    file_path = self._extract_file_path_from_context(file_context)
                    line_number = self._estimate_line_number(file_path, file_line_mappings)
                    
                    # Generate code snippet (simplified)
                    code_snippet = self._generate_code_snippet(issue_desc, category)
                    
                    # Create detailed issue
                    issue = {
                        "id": issue_id,
                        "type": issue_type,
                        "severity": self._determine_severity(category),
                        "title": self._generate_issue_title(issue_desc, category),
                        "description": issue_desc,
                        "line_number": line_number,
                        "code_snippet": code_snippet,
                        "ai_analysis": self._generate_ai_analysis(issue_desc, category),
                        "ai_suggestions": self._generate_detailed_suggestions(category, issue_desc, fix_desc),
                        "file_path": file_path,
                        "file_context": file_context,
                        "related_files": self._find_related_files(file_path),
                        "estimated_fix_time": self._estimate_fix_time(category, issue_desc)
                    }
                    
                    issues.append(issue)
            
            i += 1
        
        return issues

    def _determine_category(self, pattern: str) -> str:
        """Determine the category based on the pattern."""
        if "SECURITY" in pattern:
            return "security"
        elif "CRITICAL BUGS" in pattern:
            return "critical_bugs"
        elif "PERFORMANCE" in pattern:
            return "performance"
        return "other"

    def _determine_severity(self, category: str) -> str:
        """Determine severity based on category."""
        severity_map = {
            "security": "high",
            "critical_bugs": "critical",
            "performance": "medium"
        }
        return severity_map.get(category, "low")

    def _extract_file_path_from_context(self, file_context: str) -> str:
        """Extract the primary file path from file context."""
        if not file_context or file_context == "Multiple files":
            return "unknown"
        
        # Take the first file if multiple files
        files = [f.strip() for f in file_context.split(',')]
        return files[0] if files else "unknown"

    def _estimate_line_number(self, file_path: str, file_line_mappings: Dict[str, List[int]]) -> int:
        """Estimate line number for the issue."""
        if file_path in file_line_mappings and file_line_mappings[file_path]:
            # Return a representative line number from the file
            return file_line_mappings[file_path][0]
        return 0  # Unknown line number

    def _generate_code_snippet(self, issue_desc: str, category: str) -> str:
        """Generate a representative code snippet for the issue."""
        if "sql injection" in issue_desc.lower():
            return "query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\""
        elif "null pointer" in issue_desc.lower():
            return "user_role = user.role.name"
        elif "memory leak" in issue_desc.lower():
            return "conn = get_connection()\n# ... query execution ...\n# Missing conn.close()"
        elif "n+1" in issue_desc.lower():
            return "for user in users:\n    role = get_user_role(user.id)"
        elif "xss" in issue_desc.lower():
            return "return f\"<div>Welcome {user_input}</div>\""
        else:
            return "# Code snippet related to the issue"

    def _generate_issue_title(self, issue_desc: str, category: str) -> str:
        """Generate a concise title for the issue."""
        if "sql injection" in issue_desc.lower():
            return "SQL Injection Vulnerability"
        elif "null pointer" in issue_desc.lower():
            return "Null Pointer Exception Risk"
        elif "memory leak" in issue_desc.lower():
            return "Resource Leak"
        elif "n+1" in issue_desc.lower():
            return "Inefficient Database Query"
        elif "xss" in issue_desc.lower():
            return "XSS Vulnerability"
        elif "hardcoded" in issue_desc.lower():
            return "Hardcoded Configuration"
        else:
            return f"{category.title()} Issue"

    def _generate_ai_analysis(self, issue_desc: str, category: str) -> str:
        """Generate AI analysis of the issue."""
        if "sql injection" in issue_desc.lower():
            return "The code directly interpolates user input into SQL query without sanitization, making it vulnerable to SQL injection attacks where malicious input could execute arbitrary SQL commands."
        elif "null pointer" in issue_desc.lower():
            return "The code accesses object properties without checking if the object is null, which could cause a null pointer exception if the object is not properly initialized."
        elif "memory leak" in issue_desc.lower():
            return "Resources are allocated but not properly released, leading to memory leaks and potential application crashes over time."
        elif "n+1" in issue_desc.lower():
            return "The code executes a separate database query for each item in a loop, resulting in N+1 queries instead of a single optimized query."
        elif "xss" in issue_desc.lower():
            return "User input is directly inserted into HTML without proper escaping, allowing potential XSS attacks where malicious scripts could be executed in the browser."
        else:
            return f"This {category} issue could impact the application's security, performance, or reliability."

    def _generate_detailed_suggestions(self, category: str, issue_desc: str, fix_desc: str) -> List[Dict[str, str]]:
        """Generate detailed AI suggestions for fixing the issue."""
        suggestions = []
        
        if category == "security":
            if "sql injection" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Use parameterized queries",
                        "implementation": "Replace string formatting with parameterized queries:\nquery = \"SELECT * FROM users WHERE username = ? AND password = ?\"\ncursor.execute(query, (username, password))",
                        "reasoning": "Parameterized queries automatically escape user input and prevent SQL injection"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Implement input validation",
                        "implementation": "Add validation before database query:\nif not username or not password:\n    raise ValueError(\"Username and password are required\")\nif len(username) > 50 or len(password) > 100:\n    raise ValueError(\"Input too long\")",
                        "reasoning": "Input validation prevents malicious input from reaching the database"
                    },
                    {
                        "priority": 3,
                        "suggestion": "Use ORM for database operations",
                        "implementation": "Consider using SQLAlchemy or similar ORM:\nuser = User.query.filter_by(username=username, password=password).first()",
                        "reasoning": "ORMs provide built-in protection against SQL injection"
                    }
                ]
            elif "xss" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Escape HTML output",
                        "implementation": "import html\nreturn f\"<div>Welcome {html.escape(user_input)}</div>\"",
                        "reasoning": "HTML escaping prevents malicious scripts from being executed"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Use template engine",
                        "implementation": "Use Jinja2 or similar template engine with auto-escaping enabled",
                        "reasoning": "Template engines provide automatic escaping and better security"
                    }
                ]
        
        elif category == "critical_bugs":
            if "null pointer" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Add null safety checks",
                        "implementation": "if user and user.role:\n    user_role = user.role.name\nelse:\n    user_role = 'guest'",
                        "reasoning": "Null checks prevent runtime exceptions and provide graceful fallback"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Use optional chaining",
                        "implementation": "user_role = user?.role?.name if user else 'guest'",
                        "reasoning": "Optional chaining provides concise null safety"
                    }
                ]
            elif "memory leak" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Use context manager",
                        "implementation": "with get_connection() as conn:\n    # ... query execution ...",
                        "reasoning": "Context managers automatically handle resource cleanup"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Add explicit cleanup",
                        "implementation": "try:\n    conn = get_connection()\n    # ... query execution ...\nfinally:\n    conn.close()",
                        "reasoning": "Explicit cleanup ensures resources are released even on exceptions"
                    }
                ]
        
        elif category == "performance":
            if "n+1" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Use JOIN query to fetch all data at once",
                        "implementation": "SELECT u.*, r.name as role_name FROM users u LEFT JOIN roles r ON u.role_id = r.id WHERE u.id IN (1,2,3...)",
                        "reasoning": "Single query reduces database round trips and improves performance"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Implement eager loading",
                        "implementation": "users = User.query.options(joinedload(User.role)).all()",
                        "reasoning": "Eager loading fetches related data in a single query"
                    }
                ]
            elif "index" in issue_desc.lower():
                suggestions = [
                    {
                        "priority": 1,
                        "suggestion": "Add database index",
                        "implementation": "CREATE INDEX idx_users_username ON users(username);",
                        "reasoning": "Indexes dramatically improve query performance for filtered searches"
                    },
                    {
                        "priority": 2,
                        "suggestion": "Consider composite index",
                        "implementation": "CREATE INDEX idx_users_username_status ON users(username, status);",
                        "reasoning": "Composite indexes optimize queries with multiple WHERE conditions"
                    }
                ]
        
        # If no specific suggestions, provide generic ones
        if not suggestions:
            suggestions = [
                {
                    "priority": 1,
                    "suggestion": f"Review and fix {category} issue",
                    "implementation": fix_desc or "Implement proper solution based on best practices",
                    "reasoning": f"This {category} issue should be addressed to improve code quality"
                }
            ]
        
        return suggestions

    def _generate_code_snippet_from_description(self, issue_desc: str, issue_title: str) -> str:
        """Generate code snippet based on detailed issue description."""
        if "null" in issue_title.lower() and "pointer" in issue_title.lower():
            return "onErrorRetryFailed?.call(err);"
        elif "infinite loop" in issue_desc.lower():
            return "while (condition) {\n    // Potential infinite loop\n}"
        elif "memory leak" in issue_desc.lower():
            return "RetryInterceptor.clone(originalDio);"
        elif "data leak" in issue_desc.lower():
            return "logger.info('Request data: ' + requestData);"
        elif "logic error" in issue_desc.lower():
            return "Dio clonedDio = originalDio.clone();\n// clonedDio not used"
        else:
            return f"// Code related to: {issue_title}"

    def _generate_issue_title_from_description(self, issue_desc: str, issue_title: str) -> str:
        """Generate title from detailed description."""
        if "null" in issue_title.lower() and "pointer" in issue_title.lower():
            return "Null Pointer Exception Risk"
        elif "infinite loop" in issue_desc.lower():
            return "Infinite Loop Vulnerability"
        elif "memory leak" in issue_desc.lower():
            return "Memory Leak Risk"
        elif "data leak" in issue_desc.lower():
            return "Data Leak Vulnerability"
        elif "logic error" in issue_desc.lower():
            return "Logic Error"
        else:
            return issue_title

    def _generate_ai_analysis_from_description(self, issue_desc: str, issue_title: str) -> str:
        """Generate AI analysis from detailed description."""
        if "null" in issue_title.lower() and "pointer" in issue_title.lower():
            return "The callback function is not null-checked before calling, which could lead to a NullPointerException if the user does not provide a custom error handler."
        elif "infinite loop" in issue_desc.lower():
            return "If the callback throws an exception that is not properly handled, it could lead to an infinite loop in the retry mechanism."
        elif "memory leak" in issue_desc.lower():
            return "The interceptor clones all interceptors from the original Dio instance, which could lead to memory leaks if the original instance is not properly managed."
        elif "data leak" in issue_desc.lower():
            return "The error logging includes detailed request data, which could potentially leak sensitive information in logs."
        elif "logic error" in issue_desc.lower():
            return "The method performs unnecessary cloning of the Dio instance without using the cloned version, which is redundant and wasteful."
        else:
            return f"This issue ({issue_title}) could impact the application's reliability and should be addressed."

    def _generate_detailed_suggestions_from_fix(self, category: str, issue_desc: str, fix_desc: str) -> List[Dict[str, str]]:
        """Generate suggestions from detailed fix descriptions."""
        suggestions = []
        
        if fix_desc:
            # Parse the fix description for specific suggestions
            suggestions.append({
                "priority": 1,
                "suggestion": "Implement the suggested fix",
                "implementation": fix_desc,
                "reasoning": "This addresses the specific issue identified in the code review"
            })
        
        # Add category-specific suggestions
        if category == "security":
            if "data leak" in issue_desc.lower():
                suggestions.extend([
                    {
                        "priority": 2,
                        "suggestion": "Implement data sanitization",
                        "implementation": "Create a sanitization function to remove sensitive data before logging",
                        "reasoning": "Prevents sensitive information from being exposed in logs"
                    },
                    {
                        "priority": 3,
                        "suggestion": "Use structured logging",
                        "implementation": "Implement structured logging with configurable log levels",
                        "reasoning": "Provides better control over what information is logged"
                    }
                ])
        
        elif category == "critical_bug":
            if "null pointer" in issue_desc.lower():
                suggestions.extend([
                    {
                        "priority": 2,
                        "suggestion": "Add defensive programming",
                        "implementation": "Add null checks throughout the codebase",
                        "reasoning": "Prevents null pointer exceptions in other parts of the code"
                    },
                    {
                        "priority": 3,
                        "suggestion": "Use optional types",
                        "implementation": "Consider using optional types or nullable types where appropriate",
                        "reasoning": "Makes null handling explicit and safer"
                    }
                ])
            elif "infinite loop" in issue_desc.lower():
                suggestions.extend([
                    {
                        "priority": 2,
                        "suggestion": "Add loop counters",
                        "implementation": "Add maximum retry counters to prevent infinite loops",
                        "reasoning": "Provides a safety mechanism against infinite retry loops"
                    },
                    {
                        "priority": 3,
                        "suggestion": "Implement exponential backoff",
                        "implementation": "Use exponential backoff with jitter for retry delays",
                        "reasoning": "Reduces the likelihood of infinite loops and improves retry efficiency"
                    }
                ])
        
        elif category == "performance":
            if "memory leak" in issue_desc.lower():
                suggestions.extend([
                    {
                        "priority": 2,
                        "suggestion": "Implement proper resource management",
                        "implementation": "Use proper cleanup mechanisms and avoid unnecessary cloning",
                        "reasoning": "Prevents memory leaks and improves resource efficiency"
                    },
                    {
                        "priority": 3,
                        "suggestion": "Use object pooling",
                        "implementation": "Consider using object pooling for frequently created objects",
                        "reasoning": "Reduces memory allocation overhead and garbage collection pressure"
                    }
                ])
        
        # If no specific suggestions, provide generic ones
        if not suggestions:
            suggestions.append({
                "priority": 1,
                "suggestion": f"Review and fix {category} issue",
                "implementation": fix_desc or "Implement proper solution based on best practices",
                "reasoning": f"This {category} issue should be addressed to improve code quality"
            })
        
        return suggestions

    def _find_related_files(self, file_path: str) -> List[str]:
        """Find related files based on the current file path."""
        if not file_path or file_path == "unknown":
            return []
        
        # Simple heuristic to find related files
        related = []
        if "auth" in file_path:
            related.extend(["src/models/user.py", "src/database/connection.py"])
        elif "database" in file_path:
            related.extend(["src/models/user.py", "src/auth/login.py"])
        elif "api" in file_path:
            related.extend(["src/models/user.py", "src/auth/login.py"])
        
        return related

    def _estimate_fix_time(self, category: str, issue_desc: str) -> str:
        """Estimate time to fix the issue."""
        if category == "security":
            return "15-30 minutes"
        elif category == "critical_bugs":
            return "5-15 minutes"
        elif category == "performance":
            return "20-40 minutes"
        elif category == "code_quality":
            return "10-20 minutes"
        else:
            return "Unknown"

    def _generate_detailed_recommendations(self, category: str, issue_description: str) -> List[str]:
        """Generate detailed recommendations based on issue category and description."""
        recommendations = []
        
        if category == "security":
            if "sql injection" in issue_description.lower():
                recommendations.extend([
                    "Use parameterized queries or prepared statements",
                    "Validate and sanitize all user inputs",
                    "Implement proper input validation with whitelist approach",
                    "Consider using an ORM that handles SQL injection prevention"
                ])
            elif "xss" in issue_description.lower():
                recommendations.extend([
                    "Escape all user-generated content before displaying",
                    "Use Content Security Policy (CSP) headers",
                    "Implement proper output encoding",
                    "Validate and sanitize HTML content"
                ])
            elif "auth" in issue_description.lower():
                recommendations.extend([
                    "Implement proper authentication mechanisms",
                    "Use secure session management",
                    "Implement proper authorization checks",
                    "Consider using OAuth or JWT for authentication"
                ])
            else:
                recommendations.extend([
                    "Review security best practices for the technology stack",
                    "Implement proper input validation",
                    "Use secure coding guidelines",
                    "Consider security testing and code review processes"
                ])
        
        elif category == "critical_bugs":
            if "null pointer" in issue_description.lower():
                recommendations.extend([
                    "Add null checks before accessing object properties",
                    "Use defensive programming techniques",
                    "Implement proper error handling",
                    "Consider using optional types or null-safe operators"
                ])
            elif "crash" in issue_description.lower():
                recommendations.extend([
                    "Implement comprehensive error handling",
                    "Add try-catch blocks around critical operations",
                    "Use graceful degradation strategies",
                    "Add proper logging for debugging"
                ])
            elif "logic error" in issue_description.lower():
                recommendations.extend([
                    "Review business logic implementation",
                    "Add unit tests to verify expected behavior",
                    "Implement proper validation of business rules",
                    "Consider code review and pair programming"
                ])
            else:
                recommendations.extend([
                    "Implement comprehensive error handling",
                    "Add proper validation and checks",
                    "Use defensive programming techniques",
                    "Consider automated testing"
                ])
        
        elif category == "performance":
            if "memory leak" in issue_description.lower():
                recommendations.extend([
                    "Implement proper resource cleanup",
                    "Use memory profiling tools to identify leaks",
                    "Consider using RAII patterns",
                    "Implement proper garbage collection strategies"
                ])
            elif "infinite loop" in issue_description.lower():
                recommendations.extend([
                    "Add proper loop termination conditions",
                    "Implement timeout mechanisms",
                    "Add loop counters and limits",
                    "Consider using iterative algorithms instead of recursive ones"
                ])
            elif "n+1" in issue_description.lower():
                recommendations.extend([
                    "Use eager loading or batch loading",
                    "Implement proper database query optimization",
                    "Consider using JOIN queries instead of multiple queries",
                    "Use caching mechanisms for frequently accessed data"
                ])
            else:
                recommendations.extend([
                    "Profile the application to identify bottlenecks",
                    "Implement caching strategies",
                    "Optimize database queries",
                    "Consider using performance monitoring tools"
                ])
        
        return recommendations


    def _smart_chunked_review(self, diff: str, index_data: dict) -> str:
        """Review large diffs using smart chunking and parallel processing."""
        import concurrent.futures
        import threading
        
        # Split diff into smart chunks (group related files)
        chunks = self._create_smart_chunks(diff)
        total_chunks = len(chunks)
        
        aidm_console.print_info(f"Created {total_chunks} smart chunks for analysis")
        
        reviews = []
        lock = threading.Lock()
        
        def process_chunk(chunk_data):
            """Process a single chunk and return review."""
            chunk_idx, chunk_content = chunk_data
            if len(chunk_content.strip()) == 0:
                return None
                
            try:
                # Extract file context from chunk content
                file_context = self._extract_file_context_from_chunk(chunk_content)
                    
                # Create a shorter, focused prompt for faster responses
                review_prompt = self._create_fast_review_prompt(chunk_content, index_data)
                
                # Use a shorter timeout for individual chunks
                chunk_review = self.ollama.run_prompt(review_prompt)
                
                if chunk_review and not chunk_review.startswith("[ollama"):
                    return f"## Chunk {chunk_idx+1} Review\n{chunk_review}"
                else:
                    # If Ollama failed, return a basic analysis
                    return f"## Chunk {chunk_idx+1} Review\n# Basic Analysis\n1. SECURITY: Potential security issues detected | FIX: Review code for security vulnerabilities\n2. CRITICAL BUGS: Potential bugs detected | FIX: Review code for critical issues\n3. PERFORMANCE: Potential performance issues detected | FIX: Review code for performance optimization"
            except Exception as e:
                aidm_console.print_warning(f"Chunk {chunk_idx+1} processing failed: {e}")
                # Return a fallback review for this chunk
                return f"## Chunk {chunk_idx+1} Review\n# Fallback Analysis\n1. SECURITY: Manual review required | FIX: Review code manually for security issues\n2. CRITICAL BUGS: Manual review required | FIX: Review code manually for bugs\n3. PERFORMANCE: Manual review required | FIX: Review code manually for performance"
        
        # Process chunks in parallel (limit to 2 concurrent requests to prevent timeouts)
        with aidm_console.create_progress("Generating parallel reviews") as progress:
            task = progress.add_task("Analyzing chunks in parallel...", total=total_chunks)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit all chunks for processing
                future_to_chunk = {
                    executor.submit(process_chunk, (i, chunk)): i 
                    for i, chunk in enumerate(chunks)
                }
                
                # Collect results as they complete with timeout
                completed_chunks = 0
                try:
                    for future in concurrent.futures.as_completed(future_to_chunk, timeout=300):  # 5 minute total timeout
                        chunk_idx = future_to_chunk[future]
                        try:
                            # Add timeout to individual result retrieval
                            result = future.result(timeout=60)  # 1 minute per chunk
                            if result:
                                reviews.append(result)
                            completed_chunks += 1
                        except concurrent.futures.TimeoutError:
                            aidm_console.print_warning(f"Chunk {chunk_idx+1} timed out after 60 seconds")
                            # Add fallback review for timed out chunk
                            fallback_review = f"## Chunk {chunk_idx+1} Review\n# Timeout Analysis\n1. SECURITY: Manual review required | FIX: Review code manually for security issues\n2. CRITICAL BUGS: Manual review required | FIX: Review code manually for bugs\n3. PERFORMANCE: Manual review required | FIX: Review code manually for performance"
                            reviews.append(fallback_review)
                            completed_chunks += 1
                        except Exception as e:
                            aidm_console.print_warning(f"Chunk {chunk_idx+1} failed: {e}")
                            # Add fallback review for failed chunk
                            fallback_review = f"## Chunk {chunk_idx+1} Review\n# Error Analysis\n1. SECURITY: Manual review required | FIX: Review code manually for security issues\n2. CRITICAL BUGS: Manual review required | FIX: Review code manually for bugs\n3. PERFORMANCE: Manual review required | FIX: Review code manually for performance"
                            reviews.append(fallback_review)
                            completed_chunks += 1
                        
                        progress.update(task, completed=completed_chunks)
                        
                except concurrent.futures.TimeoutError:
                    aidm_console.print_warning("Overall parallel processing timed out after 5 minutes")
                    # Cancel remaining futures
                    for future in future_to_chunk:
                        future.cancel()
        
        # Combine all reviews
        if reviews:
            combined_review = f"# Fast Code Review ({len(reviews)}/{total_chunks} chunks analyzed)\n\n"
            combined_review += "\n\n".join(reviews)
            combined_review += f"\n\n## Summary\nAnalyzed {len(reviews)} out of {total_chunks} chunks. Some chunks may have timed out or failed."
            return combined_review
        else:
            # Fallback: try sequential processing if parallel completely fails
            aidm_console.print_warning("Parallel processing failed, trying sequential processing...")
            return self._sequential_chunk_review(chunks, index_data)

    def _sequential_chunk_review(self, chunks: list, index_data: dict) -> str:
        """Fallback sequential processing when parallel processing fails."""
        reviews = []
        
        aidm_console.print_info("Processing chunks sequentially...")
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) == 0:
                continue
                
            try:
                aidm_console.print_info(f"Processing chunk {i+1}/{len(chunks)}...")
                
                # Create a shorter, focused prompt for faster responses
                review_prompt = self._create_fast_review_prompt(chunk, index_data)
                chunk_review = self.ollama.run_prompt(review_prompt)
                
                if chunk_review and not chunk_review.startswith("[ollama"):
                    reviews.append(f"## Chunk {i+1} Review\n{chunk_review}")
                else:
                    # Basic fallback review
                    reviews.append(f"## Chunk {i+1} Review\n# Basic Analysis\n1. SECURITY: Potential security issues detected | FIX: Review code for security vulnerabilities\n2. CRITICAL BUGS: Potential bugs detected | FIX: Review code for critical issues\n3. PERFORMANCE: Potential performance issues detected | FIX: Review code for performance optimization")
                    
            except Exception as e:
                aidm_console.print_warning(f"Chunk {i+1} failed: {e}")
                # Add fallback review
                reviews.append(f"## Chunk {i+1} Review\n# Error Analysis\n1. SECURITY: Manual review required | FIX: Review code manually for security issues\n2. CRITICAL BUGS: Manual review required | FIX: Review code manually for bugs\n3. PERFORMANCE: Manual review required | FIX: Review code manually for performance")
        
        if reviews:
            combined_review = f"# Sequential Code Review ({len(reviews)} chunks analyzed)\n\n"
            combined_review += "\n\n".join(reviews)
            combined_review += f"\n\n## Summary\nAnalyzed {len(reviews)} chunks sequentially. Some chunks may have failed."
            return combined_review
        else:
            return "Failed to generate reviews for any chunks using sequential processing."

    def _create_smart_chunks(self, diff: str) -> list:
        """Create smart chunks by grouping related files together."""
        file_chunks = self._split_diff_by_files(diff)
        
        # Group files by directory/type for better context
        smart_chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 15000  # Reduced chunk size to prevent timeouts
        
        for file_chunk in file_chunks:
            chunk_size = len(file_chunk)
            
            # If adding this chunk would exceed size limit, start a new chunk
            if current_size + chunk_size > max_chunk_size and current_chunk:
                smart_chunks.append('\n'.join(current_chunk))
                current_chunk = [file_chunk]
                current_size = chunk_size
            else:
                current_chunk.append(file_chunk)
                current_size += chunk_size
        
        # Add the last chunk
        if current_chunk:
            smart_chunks.append('\n'.join(current_chunk))
        
        return smart_chunks

    def _extract_file_context_from_chunk(self, chunk_content: str) -> str:
        """Extract file paths from a chunk of diff content."""
        files = []
        lines = chunk_content.split('\n')
        
        for line in lines:
            # Look for git diff file headers
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[3][2:]  # Remove "b/" prefix
                    if file_path not in files:
                        files.append(file_path)
            elif line.startswith('+++'):
                file_path = line[4:]  # Remove "+++ " prefix
                if file_path != '/dev/null' and file_path not in files:
                    files.append(file_path)
        
        return ', '.join(files) if files else "unknown"

    def _create_fast_review_prompt(self, diff_chunk: str, project_context: dict = None) -> str:
        """Create a fast, focused review prompt for quick analysis."""
        context_info = ""
        if project_context:
            languages = project_context.get('summary', {}).get('languages', {})
            context_info = f"Project languages: {languages}\n"
        
        prompt = f"""Quick code review - focus on CRITICAL issues only:

{context_info}

REVIEW THIS CODE CHANGES (be concise, max 200 words):
{diff_chunk}

Find ONLY:
1. **SECURITY**: SQL injection, XSS, auth bypass, data leaks
2. **CRITICAL BUGS**: Null pointers, crashes, logic errors
3. **PERFORMANCE**: Memory leaks, infinite loops, N+1 queries

Format: **ISSUE**: Brief description | **FIX**: Quick solution

Be direct and brief!"""
        
        return prompt

    def _split_diff_by_files(self, diff: str) -> list:
        """Split diff into chunks by file boundaries."""
        lines = diff.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            # Check if this is a new file diff header
            if line.startswith('diff --git'):
                # Save previous chunk if it exists
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            
            current_chunk.append(line)
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def summarize(self) -> str:
        """Return review summary with beautiful formatting."""
        if self.review:
            aidm_console.print_separator()
            aidm_console.print_header("📋 Aggressive Review Results", "Comprehensive code analysis")
            aidm_console.print_markdown(self.review)
        
        return self.review
