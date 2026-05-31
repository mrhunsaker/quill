from __future__ import annotations

from quill.core.yaml_structure import (
    add_yaml_child,
    add_yaml_sibling,
    delete_yaml_node,
    extract_yaml_nodes,
    rename_yaml_node,
)


def test_extract_yaml_nodes_tracks_hierarchy() -> None:
    text = "root:\n  child: value\n  items:\n    - first\n"
    nodes = extract_yaml_nodes(text)
    assert [node.label for node in nodes] == ["root"]
    assert [node.label for node in nodes[0].children] == ["child", "items"]
    assert [node.label for node in nodes[0].children[1].children] == ["first"]


def test_add_and_delete_yaml_nodes_preserve_indentation() -> None:
    text = "root:\n"
    updated = add_yaml_child(text, 0, "mapping", "child")
    assert updated == "root:\n  child:\n"
    updated = add_yaml_sibling(updated, 0, "mapping", "next")
    assert updated == "root:\n  child:\nnext:\n"
    updated = delete_yaml_node(updated, 0)
    assert updated == "next:\n"


def test_rename_yaml_node_updates_mapping_and_sequence_items() -> None:
    text = "root:\n  child: value\n  items:\n    - first\n"
    updated = rename_yaml_node(text, 1, "renamed child")
    assert '"renamed child": value' in updated
    updated = rename_yaml_node(updated, 3, "second")
    assert "- second" in updated
