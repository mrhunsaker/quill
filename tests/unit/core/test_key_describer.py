from quill.core.key_describer import command_for_accelerator, normalize_accelerator


def test_normalize_is_case_and_space_insensitive() -> None:
    assert normalize_accelerator("Ctrl + Shift+P") == "ctrl+shift+p"


def test_normalize_multichord() -> None:
    assert normalize_accelerator("Ctrl+Shift+Grave, Tab") == "ctrl+shift+grave, tab"


def test_command_for_accelerator_found() -> None:
    keymap = {"file.save": "Ctrl+S", "app.command_palette": "Ctrl+Shift+P"}
    assert command_for_accelerator(keymap, "ctrl+s") == "file.save"


def test_command_for_accelerator_not_found() -> None:
    keymap = {"file.save": "Ctrl+S"}
    assert command_for_accelerator(keymap, "Ctrl+Q") is None


def test_command_for_accelerator_ignores_empty_binding() -> None:
    keymap = {"format.join_lines": "", "file.save": "Ctrl+S"}
    assert command_for_accelerator(keymap, "") is None
