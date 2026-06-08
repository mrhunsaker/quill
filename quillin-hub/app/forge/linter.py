import subprocess
import os
import shutil
import json
from typing import Dict, Any
from .security_scanner import SecurityWatchdog

def audit_submission(upload_path: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    End-to-end audit of a Quillin submission.
    Combines structural linting and security analysis.
    """
    results = {
        "status": "PASS",
        "reports": {
            "linter": None,
            "security": None,
            "watchdog": None
        }
    }

    # 1. Structural Linting (using the actual QUILL tool)
    try:
        lint_proc = subprocess.run(
            ["python", "-m", "quill.tools.quillin_lint", upload_path, "--strict"],
            capture_output=True, text=True
        )
        if lint_proc.returncode != 0:
            results["status"] = "FAIL"
            results["reports"]["linter"] = lint_proc.stdout
    except Exception as e:
        results["status"] = "ERROR"
        results["reports"]["linter"] = f"Linter execution error: {str(e)}"

    # 2. Security Scanning (Bandit)
    try:
        bandit_proc = subprocess.run(
            ["bandit", "-r", upload_path, "-f", "json"],
            capture_output=True, text=True
        )
        # Bandit returns 0 if no issues, 1 if issues found
        if bandit_proc.returncode != 0:
            # We only fail the whole submission if there are HIGH severity issues
            security_data = json.loads(bandit_proc.stdout)
            high_issues = [i for i in security_data.get('results', []) if i['issue_severity'] == 'HIGH']
            if high_issues:
                results["status"] = "FAIL"
                results["reports"]["security"] = "High-severity security vulnerabilities detected via Bandit."
            else:
                results["reports"]["security"] = "Minor security warnings detected."
    except Exception as e:
        results["reports"]["security"] = f"Security scan error: {str(e)}"

    # 3. Capability Honesty (AST Watchdog)
    # Expects the user to have a main module defined in manifest
    main_module = manifest.get('main', 'extension')
    py_file = os.path.join(upload_path, f"{main_module}.py")
    
    if os.path.exists(py_file):
        watchdog = SecurityWatchdog(manifest)
        watchdog_issues = watchdog.scan_file(py_file)
        if watchdog_issues:
            results["status"] = "FAIL"
            results["reports"]["watchdog"] = "\n".join([f"Line {ln}: {msg}" for ln, msg in watchdog_issues])
    elif manifest.get('capabilities'):
        # If capabilities are declared but no python code exists, that's a mismatch
        results["status"] = "FAIL"
        results["reports"]["watchdog"] = "Capabilities declared but no implementation file found."

    return results
