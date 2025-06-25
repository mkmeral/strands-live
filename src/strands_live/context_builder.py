"""
Context builder for Strands Live Speech Agent.

This module provides functionality to automatically gather context from the current
directory and relevant files to enhance the agent's awareness of the working environment.
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union


class ContextBuilder:
    """Builds context information for the speech agent."""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize the context builder.
        
        Args:
            base_path: Base directory to gather context from. Defaults to current directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        
    def get_directory_context(self, max_depth: int = 2, max_files: int = 20) -> str:
        """Get directory structure context.
        
        Args:
            max_depth: Maximum depth to traverse
            max_files: Maximum number of files to list
            
        Returns:
            Formatted directory structure string
        """
        try:
            # Get directory tree structure
            tree_output = self._get_directory_tree(max_depth=max_depth, max_files=max_files)
            
            return f"""
## Current Directory Structure

**Working Directory:** `{self.base_path.absolute()}`

```
{tree_output}
```
"""
        except Exception as e:
            return f"## Current Directory\n**Working Directory:** `{self.base_path.absolute()}`\n*Error getting directory structure: {e}*\n"
    
    def _get_directory_tree(self, max_depth: int = 2, max_files: int = 20) -> str:
        """Get directory tree using system tree command or manual traversal."""
        try:
            # Try using system 'tree' command first
            result = subprocess.run(
                ['tree', '-L', str(max_depth), '-a', '--dirsfirst', str(self.base_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Fallback to manual directory traversal
        return self._manual_directory_tree(max_depth=max_depth, max_files=max_files)
    
    def _manual_directory_tree(self, max_depth: int = 2, max_files: int = 20) -> str:
        """Manually create directory tree."""
        lines = []
        file_count = 0
        
        def _traverse(path: Path, prefix: str = "", depth: int = 0):
            nonlocal file_count
            if depth > max_depth or file_count >= max_files:
                return
                
            try:
                items = list(path.iterdir())
                # Sort: directories first, then files
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                
                for i, item in enumerate(items):
                    if file_count >= max_files:
                        lines.append(f"{prefix}├── ... (truncated)")
                        break
                        
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{current_prefix}{item.name}")
                    file_count += 1
                    
                    if item.is_dir() and depth < max_depth:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        _traverse(item, next_prefix, depth + 1)
                        
            except PermissionError:
                lines.append(f"{prefix}├── [Permission Denied]")
        
        lines.append(str(self.base_path.name))
        _traverse(self.base_path, "", 0)
        return "\n".join(lines)

    def get_file_context(self, file_patterns: List[str] = None) -> str:
        """Get context from relevant files in the directory.
        
        Args:
            file_patterns: List of file patterns to look for. 
                          Defaults to ['README.md', 'AmazonQ.md', 'CHANGELOG.md']
                          
        Returns:
            Formatted file contents
        """
        if file_patterns is None:
            file_patterns = ['README.md', 'AmazonQ.md', 'CHANGELOG.md', 'package.json', 'pyproject.toml']
        
        context_parts = []
        
        for pattern in file_patterns:
            file_path = self.base_path / pattern
            if file_path.exists() and file_path.is_file():
                content = self._read_file_safely(file_path)
                if content:
                    context_parts.append(f"""
## {pattern}

```
{content}
```
""")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _read_file_safely(self, file_path: Path, max_lines: int = 100) -> Optional[str]:
        """Safely read file content with size limits.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to read
            
        Returns:
            File content or None if unable to read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append("... (truncated)")
                        break
                    lines.append(line.rstrip())
                return "\n".join(lines)
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            return f"[Error reading file: {e}]"
    
    def get_git_context(self) -> str:
        """Get Git repository context if available."""
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                capture_output=True,
                text=True,
                cwd=self.base_path,
                timeout=2
            )
            
            if result.returncode != 0:
                return ""
            
            # Get current branch and recent commits
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=self.base_path,
                timeout=2
            )
            
            log_result = subprocess.run(
                ['git', 'log', '--oneline', '-5'],
                capture_output=True,
                text=True,
                cwd=self.base_path,
                timeout=2
            )
            
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                cwd=self.base_path,
                timeout=2
            )
            
            git_info = []
            
            if branch_result.returncode == 0 and branch_result.stdout.strip():
                git_info.append(f"**Current Branch:** `{branch_result.stdout.strip()}`")
            
            if log_result.returncode == 0:
                git_info.append(f"**Recent Commits:**\n```\n{log_result.stdout.strip()}\n```")
            
            if status_result.returncode == 0 and status_result.stdout.strip():
                git_info.append(f"**Working Directory Status:**\n```\n{status_result.stdout.strip()}\n```")
            
            if git_info:
                return f"""## Git Repository Context

{chr(10).join(git_info)}
"""
            
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return ""
    
    def build_full_context(self, 
                          include_directory: bool = True,
                          include_files: bool = True, 
                          include_git: bool = True,
                          file_patterns: List[str] = None) -> str:
        """Build complete context information.
        
        Args:
            include_directory: Include directory structure
            include_files: Include relevant file contents
            include_git: Include git repository information
            file_patterns: Custom file patterns to include
            
        Returns:
            Complete context string
        """
        context_parts = []
        
        if include_directory:
            dir_context = self.get_directory_context()
            if dir_context.strip():
                context_parts.append(dir_context)
        
        if include_git:
            git_context = self.get_git_context()
            if git_context.strip():
                context_parts.append(git_context)
        
        if include_files:
            file_context = self.get_file_context(file_patterns)
            if file_context.strip():
                context_parts.append(file_context)
        
        if not context_parts:
            return ""
        
        return f"""
# Project Context

{chr(10).join(context_parts)}

---

*This context was automatically gathered to help me understand your project structure and current working environment.*
"""


def create_enhanced_system_prompt(base_prompt: str = None, 
                                  context_builder: ContextBuilder = None,
                                  **context_options) -> str:
    """Create an enhanced system prompt with project context.
    
    Args:
        base_prompt: Base system prompt. Uses default if None.
        context_builder: ContextBuilder instance. Creates new if None.
        **context_options: Options to pass to build_full_context()
        
    Returns:
        Enhanced system prompt with context
    """
    if base_prompt is None:
        base_prompt = (
            "You are a helpful assistant based on Strands Agents. You can access internet, customer's files and AWS account through tools. "
            "Help user achieve their goal. Keep the interaction conversational. "
            "When reading order numbers, please read each digit individually, separated by pauses. For example, order #1234 should be read as 'order number one-two-three-four' rather than 'order number one thousand two hundred thirty-four'."
        )
    
    if context_builder is None:
        context_builder = ContextBuilder()
    
    project_context = context_builder.build_full_context(**context_options)
    
    if project_context.strip():
        return f"{base_prompt}\n\n{project_context}"
    else:
        return base_prompt