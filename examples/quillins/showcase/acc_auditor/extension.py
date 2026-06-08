from quill import api

def run_audit(context):
    """
    Analyzes the current document for common accessibility pitfalls.
    """
    text = api.get_all_text()
    issues = []

    # Rule 1: Heading Hierarchy
    # Simple check for skipping H1 -> H3
    lines = text.splitlines()
    last_level = 0
    for line in lines:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level > last_level + 1:
                issues.append(f"Heading Level Skip: Found { '#' * level } after { '#' * last_level }")
            last_level = level

    # Rule 2: Empty Alt Text markers
    if "[Image]" in text and "Alt:" not in text:
        issues.append("Found image marker without alternative text description.")

    # Rule 3: Redundant punctuation (Screen reader noise)
    if "!!!" in text or "???" in text:
        issues.append("Redundant punctuation detected (can be noisy for screen readers).")

    if not issues:
        api.announce("Accessibility Audit: No immediate issues found. Great work!")
    else:
        report = "\n".join([f"Issue {i+1}: {msg}" for i, msg in enumerate(issues)])
        api.insert_text(f"\n--- Accessibility Audit Report ---\n{report}\n")
        api.announce(f"Audit complete. Found {len(issues)} accessibility issues.")

api.register_command("run_audit", run_audit)
