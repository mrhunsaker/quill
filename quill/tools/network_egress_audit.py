"""No-silent-network gate (GATE-9).

Every outbound network call in Quill must be deliberate, reviewed, and tied to
an explicit user action or an explicitly consented background check. This gate
inventories every egress call site in the ``quill`` package via AST and fails if
a new one appears that is not recorded in ``_REVIEWED_EGRESS`` with a rationale.

The rationale for each site documents *what triggers it* and *why it is not a
silent call* (a user action, a visible progress/consent surface, or an opt-in
setting). A reviewer adding a new network call must add it here, which forces a
conscious decision and a code-review touchpoint.

This is the structural half of GATE-9. The runtime half — asserting the AI chat
path shows provider, model, and scope before any cloud call — lands with the
provider-wiring work (AI-13), where that call path first exists.
"""

from __future__ import annotations

import ast
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# Egress function names. A call whose function is one of these (by attribute or
# bare name) counts as a network call for inventory purposes.
_EGRESS_CALLEES = frozenset({
    "urlopen",
    "urlretrieve",
})

# Reviewed, allowed egress sites: "<relative path>::<enclosing function>" mapped
# to the reason the call is not silent. Update this when adding a network call.
_REVIEWED_EGRESS: dict[str, str] = {
    "ui/main_frame.py::open_url": (
        "User types a URL in the Open from URL dialog and confirms a 'Download "
        "from <host> (<size>)?' prompt before any body is fetched."
    ),
    "core/dectalk_runtime.py::download_dectalk_runtime": (
        "User explicitly installs the optional DECTALK voice runtime; download "
        "runs with a verified TLS context and visible progress."
    ),
    "core/updates.py::fetch_update_manifest": (
        "Update check; gated by the user's update-check setting and shown in the "
        "update UI. Verified TLS."
    ),
    "core/updates.py::fetch_latest_release": (
        "Update check against GitHub Releases; same update setting and UI."
    ),
    "core/updates.py::fetch_releases": (
        "Fetches release notes for an update the user is already reviewing."
    ),
    "core/updates.py::download_release_asset": (
        "User chooses to download an offered update; verified TLS, visible progress."
    ),
    "core/glow_updates.py::fetch_glow_manifest": (
        "Opt-in GLOW engine update check (GLOW-8); runs only when the user invokes "
        "'Check for GLOW Updates' or enables the GLOW auto-check setting. Fetches a "
        "signed manifest over a verified TLS context and host-allow-listed HTTPS URL."
    ),
    "core/assistant_ai.py::_fetch_models_from_endpoint": (
        "User-initiated model discovery from the AI Connection dialog (Verify "
        "Connection / List Models). HTTPS uses a verified context."
    ),
    "core/assistant_ai.py::_post_chat": (
        "AI generation against the user's explicitly configured provider (AI-13). "
        "Only runs when the user has set up an AI connection and invokes an "
        "assistant action; HTTPS uses a verified context and cloud endpoints are "
        "HTTPS-enforced by _validate_endpoint_security."
    ),
    "core/assistant_ai.py::_post_chat_stream": (
        "Streaming variant of AI generation (AI-14). Same gating as _post_chat: "
        "only runs against the user's explicitly configured, non-off provider on "
        "an explicit assistant action, with HTTPS enforced for cloud endpoints by "
        "_validate_endpoint_security and a verified TLS context."
    ),
    "core/ai/model_manager.py::_download": (
        "User-initiated local AI model download; verified TLS for HTTPS, visible progress callback."
    ),
    "core/lexical.py::_http_get_json": (
        "Consented online dictionary/thesaurus lookups (DICT-1: Free Dictionary "
        "and Datamuse). Only runs when the user enables online lexical lookups; "
        "HTTPS with a verified TLS context, no API key, graceful offline fallback."
    ),
    "ui/main_frame_quillins.py::fetch": (
        "Quillin host 'net' capability bridge. A Quillin can only reach this "
        "method when its manifest declares the default-deny 'net' capability AND "
        "the user grants explicit per-action consent at the runtime consent gate "
        "(_EditorHostServices reaches fetch only after the host's capability + "
        "consent check passes); there is no silent path."
    ),
}


def _enclosing_function_name(tree: ast.AST, target: ast.AST) -> str:
    """Return the nearest enclosing def/async-def name for ``target``."""
    best = "<module>"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for descendant in ast.walk(node):
                if descendant is target:
                    best = node.name
                    # Keep walking: a more deeply nested function is a better
                    # match, and ast.walk visits outer nodes first.
    return best


def _callee_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def discover_egress_sites() -> dict[str, str]:
    """Return {"<rel path>::<function>": "<source line text>"} for every call."""
    sites: dict[str, str] = {}
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _callee_name(node) in _EGRESS_CALLEES:
                rel = path.relative_to(_PACKAGE_ROOT).as_posix()
                func_name = _enclosing_function_name(tree, node)
                sites[f"{rel}::{func_name}"] = func_name
    return sites


def find_unreviewed_egress() -> tuple[set[str], set[str]]:
    """Return (unreviewed_sites, stale_reviewed_entries)."""
    discovered = set(discover_egress_sites())
    reviewed = set(_REVIEWED_EGRESS)
    return discovered - reviewed, reviewed - discovered
