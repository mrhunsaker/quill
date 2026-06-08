import ast
import os
from typing import List, Tuple

class SecurityWatchdog:
    """
    Static Analysis Watchdog for Quillin extensions.
    Analyzes source code for security vulnerabilities and capability honesty.
    """
    
    # Banned modules that often indicate sandbox escape attempts
    BANNED_MODULES = {
        'ctypes', 
        'pickle', 
        'marshal', 
        'builtin_function_or_method',
        'platformdirs' # Use QUILL's internal API instead
    }
    
    # Modules that require specific capabilities
    CAPABILITY_MAP = {
        'os': 'fs',
        'shutil': 'fs',
        'glob': 'fs',
        'requests': 'net',
        'urllib': 'net',
        'http': 'net',
        'socket': 'net',
        'threading': 'stability',
        'multiprocessing': 'stability'
    }

    def __init__(self, manifest):
        self.manifest = manifest
        self.declared_capabilities = set(manifest.get('capabilities', []))

    def scan_file(self, file_path: str) -> List[Tuple[int, str]]:
        """
        Scans a python file using AST to find security and watchdog issues.
        Returns a list of (line_number, issue_message).
        """
        issues = []
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                return [(e.lineno, f"Syntax Error: {e.msg}")]

        for node in ast.walk(tree):
            # Check for Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    issue = self._check_module(alias.name, node.lineno)
                    if issue: issues.append(issue)
            
            elif isinstance(node, ast.ImportFrom):
                issue = self._check_module(node.module, node.lineno)
                if issue: issues.append(issue)
                
            # Check for dangerous function calls (eval, exec)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ('eval', 'exec'):
                        issues.append((node.lineno, f"CRITICAL: Forbidden use of {node.func.id()}(). Sandbox escape risk."))

        return issues

    def _check_module(self, module_name: str, line_no: int) -> Tuple[int, str] = None:
        if not module_name:
            return None
            
        # 1. Check for outright banned modules
        if module_name in self.BANNED_MODULES:
            return (line_no, f"SECURITY: Use of banned module '{module_name}' is strictly forbidden.")
        
        # 2. Check for capability honesty
        for mod, cap in self.CAPABILITY_MAP.items():
            if module_name == mod or module_name.startswith(f"{mod}."):
                if cap not in self.declared_capabilities:
                    return (line_no, f"WATCHDOG: Module '{module_name}' requires '{cap}' capability, which is not declared in manifest.")
        
        return None
