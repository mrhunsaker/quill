from __future__ import annotations

from collections.abc import Callable

from quill.core.assistant import (
    assistant_prompt_presets,
    build_assistant_tools,
    rank_assistant_tools,
    render_assistant_prompt,
)
from quill.core.assistant_agents import agent_profiles, build_agent_plan
from quill.core.assistant_ai import (
    AssistantConnectionSettings,
    ModelRecommendation,
    default_host_for_provider,
    default_model_for_provider,
    filter_model_names,
    list_assistant_models,
    load_assistant_api_key,
    load_assistant_connection_settings,
    provider_api_key_label,
    provider_help_text,
    provider_requires_api_key,
    recommended_model_guidance,
    save_assistant_api_key,
    save_assistant_connection_settings,
    verify_assistant_connection,
)
from quill.core.assistant_prompts import (
    CustomPrompt,
    delete_custom_prompt,
    generate_prompt_id,
    load_custom_prompts,
    render_prompt_template,
    template_variables,
    unknown_template_variables,
    upsert_custom_prompt,
)
from quill.core.commands import CommandRegistry
from quill.core.features import FeatureManager
from quill.core.python_sandbox import PythonSandboxResult, run_python_sandbox


class RunPythonDialog:
    def __init__(
        self,
        parent: object,
        *,
        document_text: str,
        selection_text: str,
        outline: list[dict[str, object]] | None = None,
        apply_callback: Callable[[str], None],
    ) -> None:
        import wx

        self._wx = wx
        self._document_text = document_text
        self._selection_text = selection_text
        self._outline = outline
        self._apply_callback = apply_callback
        self._latest_result: PythonSandboxResult | None = None

        self.dialog = wx.Dialog(
            parent,
            title="Run Python",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((900, 680))

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "Sandboxed Python can read document_text and selection_text. "
                    "Set result or print output, then apply the transformed text."
                ),
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        self.code = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB | wx.BORDER_SIMPLE,
            size=(-1, 280),
        )
        self.code.SetValue(
            "# document_text and selection_text are available.\n"
            "# Set result or call set_result(...).\n"
            "result = selection_text or document_text\n"
        )
        root.Add(self.code, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.status = wx.StaticText(self.dialog, label="Ready.")
        root.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.preview = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 220),
        )
        root.Add(self.preview, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.run_button = wx.Button(self.dialog, label="Run")
        self.apply_button = wx.Button(self.dialog, label="Apply Result")
        self.close_button = wx.Button(self.dialog, id=wx.ID_CANCEL, label="Close")
        self.apply_button.Enable(False)
        buttons.Add(self.run_button, 0, wx.RIGHT, 8)
        buttons.Add(self.apply_button, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close_button, 0)
        root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.dialog.SetSizer(root)
        self.run_button.Bind(wx.EVT_BUTTON, self._on_run)
        self.apply_button.Bind(wx.EVT_BUTTON, self._on_apply)
        self.close_button.Bind(wx.EVT_BUTTON, lambda _e: self.dialog.EndModal(wx.ID_CANCEL))
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        self.code.SetFocus()

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _on_char_hook(self, event: object) -> None:
        if event.GetKeyCode() == self._wx.WXK_ESCAPE:
            self.dialog.EndModal(self._wx.ID_CANCEL)
            return
        event.Skip()

    def _on_run(self, _event: object) -> None:
        result = run_python_sandbox(
            self.code.GetValue(),
            document_text=self._document_text,
            selection_text=self._selection_text,
            outline=self._outline,
        )
        self._latest_result = result
        self.preview.SetValue(self._render_result(result))
        self.apply_button.Enable(
            result.succeeded and bool((result.result or result.stdout).strip())
        )
        if result.succeeded:
            self.status.SetLabel(f"Completed in {result.elapsed_seconds:.2f}s.")
            return
        if result.timed_out:
            self.status.SetLabel("Execution timed out.")
            return
        if result.error:
            self.status.SetLabel("Execution failed.")
            return
        self.status.SetLabel("Execution finished.")

    def _on_apply(self, _event: object) -> None:
        if self._latest_result is None:
            return
        updated = self._latest_result.result.strip() or self._latest_result.stdout.strip()
        if not updated:
            return
        self._apply_callback(updated)
        self.dialog.EndModal(self._wx.ID_OK)

    def _render_result(self, result: PythonSandboxResult) -> str:
        parts = [
            f"Return code: {result.returncode}",
            f"Timed out: {result.timed_out}",
            "",
        ]
        if result.result:
            parts.extend(("Result:", result.result, ""))
        if result.stdout:
            parts.extend(("Stdout:", result.stdout, ""))
        if result.stderr:
            parts.extend(("Stderr:", result.stderr, ""))
        if result.error:
            parts.extend(("Error:", result.error, ""))
        return "\n".join(parts).strip()


class PromptStudioDialog:
    def __init__(
        self,
        parent: object,
        *,
        selection_text: str,
        document_text: str,
        on_use_prompt: Callable[[str], None],
        announce: Callable[[str], None] | None = None,
    ) -> None:
        import wx

        self._wx = wx
        self._selection_text = selection_text
        self._document_text = document_text
        self._use_prompt_callback = on_use_prompt
        self._announce = announce or (lambda _message: None)
        self._custom_prompts = load_custom_prompts()
        self._custom_by_id = {prompt.prompt_id: prompt for prompt in self._custom_prompts}
        self._builtin = assistant_prompt_presets()

        self.dialog = wx.Dialog(
            parent,
            title="Prompt Studio",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((980, 680))

        root = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        right = wx.BoxSizer(wx.VERTICAL)

        left.Add(
            wx.StaticText(self.dialog, label="Prompt Library"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            8,
        )
        self.prompt_list = wx.ListBox(self.dialog)
        left.Add(self.prompt_list, 1, wx.EXPAND | wx.ALL, 8)
        self.new_button = wx.Button(self.dialog, label="New Custom Prompt")
        self.delete_button = wx.Button(self.dialog, label="Delete Custom Prompt")
        self.use_button = wx.Button(self.dialog, label="Use in Writing Assistant")
        left_actions = wx.BoxSizer(wx.HORIZONTAL)
        left_actions.Add(self.new_button, 0, wx.RIGHT, 8)
        left_actions.Add(self.delete_button, 0, wx.RIGHT, 8)
        left_actions.Add(self.use_button, 0)
        left.Add(left_actions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        right.Add(wx.StaticText(self.dialog, label="Title"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.title_text = wx.TextCtrl(self.dialog)
        right.Add(self.title_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        right.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "Template (variables: {selection} {document} "
                    "{tone} {audience} {goal})"
                ),
            ),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            8,
        )
        self.template_text = wx.TextCtrl(self.dialog, style=wx.TE_MULTILINE, size=(-1, 220))
        right.Add(self.template_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self.dialog, label="Tone"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.tone_text = wx.TextCtrl(self.dialog)
        row.Add(self.tone_text, 1, wx.RIGHT, 8)
        row.Add(
            wx.StaticText(self.dialog, label="Audience"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.audience_text = wx.TextCtrl(self.dialog)
        row.Add(self.audience_text, 1)
        right.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        right.Add(wx.StaticText(self.dialog, label="Goal"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.goal_text = wx.TextCtrl(self.dialog)
        right.Add(self.goal_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        preview_actions = wx.BoxSizer(wx.HORIZONTAL)
        self.preview_button = wx.Button(self.dialog, label="Preview Render")
        self.save_button = wx.Button(self.dialog, label="Save Custom Prompt")
        preview_actions.Add(self.preview_button, 0, wx.RIGHT, 8)
        preview_actions.Add(self.save_button, 0)
        right.Add(preview_actions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.preview = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 180),
        )
        right.Add(self.preview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.status = wx.StaticText(self.dialog, label="Ready.")
        right.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        root.Add(left, 1, wx.EXPAND)
        root.Add(right, 2, wx.EXPAND)
        self.dialog.SetSizer(root)

        self.prompt_list.Bind(wx.EVT_LISTBOX, self._on_selected_prompt_changed)
        self.new_button.Bind(wx.EVT_BUTTON, self._on_new_prompt)
        self.delete_button.Bind(wx.EVT_BUTTON, self._on_delete_prompt)
        self.use_button.Bind(wx.EVT_BUTTON, self._on_use_prompt_clicked)
        self.preview_button.Bind(wx.EVT_BUTTON, self._on_preview_prompt)
        self.save_button.Bind(wx.EVT_BUTTON, self._on_save_prompt)

        self._selected_prompt_key = ""
        self._refresh_prompt_list()

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _refresh_prompt_list(self) -> None:
        labels: list[str] = []
        keys: list[str] = []
        for preset in self._builtin:
            labels.append(f"Built-in: {preset.title}")
            keys.append(f"builtin:{preset.name}")
        for prompt in self._custom_prompts:
            labels.append(f"Custom: {prompt.title}")
            keys.append(f"custom:{prompt.prompt_id}")
        self._keys = keys
        self.prompt_list.Set(labels)
        if keys:
            self.prompt_list.SetSelection(0)
            self._selected_prompt_key = keys[0]
            self._load_selected_prompt()
        else:
            self._selected_prompt_key = ""
            self.title_text.SetValue("")
            self.template_text.SetValue("")
            self.preview.SetValue("")

    def _on_selected_prompt_changed(self, _event: object) -> None:
        selection = self.prompt_list.GetSelection()
        if selection == self._wx.NOT_FOUND:
            return
        if selection < 0 or selection >= len(self._keys):
            return
        self._selected_prompt_key = self._keys[selection]
        self._load_selected_prompt()

    def _load_selected_prompt(self) -> None:
        key = self._selected_prompt_key
        if key.startswith("builtin:"):
            preset_name = key.removeprefix("builtin:")
            preset = next((item for item in self._builtin if item.name == preset_name), None)
            if preset is None:
                return
            self.title_text.SetValue(preset.title)
            self.template_text.SetValue(preset.template)
            self.save_button.Enable(False)
            self.delete_button.Enable(False)
            self.status.SetLabel("Loaded built-in prompt.")
            self._render_preview()
            return
        if key.startswith("custom:"):
            prompt_id = key.removeprefix("custom:")
            prompt = self._custom_by_id.get(prompt_id)
            if prompt is None:
                return
            self.title_text.SetValue(prompt.title)
            self.template_text.SetValue(prompt.template)
            self.save_button.Enable(True)
            self.delete_button.Enable(True)
            self.status.SetLabel("Loaded custom prompt.")
            self._render_preview()

    def _on_new_prompt(self, _event: object) -> None:
        self._selected_prompt_key = f"custom:{generate_prompt_id()}"
        self.title_text.SetValue("")
        self.template_text.SetValue(
            "Goal: {goal}\nAudience: {audience}\nTone: {tone}\n\n{selection}"
        )
        self.save_button.Enable(True)
        self.delete_button.Enable(False)
        self.status.SetLabel("Creating a new custom prompt.")
        self.preview.SetValue("")

    def _on_delete_prompt(self, _event: object) -> None:
        key = self._selected_prompt_key
        if not key.startswith("custom:"):
            return
        prompt_id = key.removeprefix("custom:")
        self._custom_prompts = delete_custom_prompt(prompt_id)
        self._custom_by_id = {prompt.prompt_id: prompt for prompt in self._custom_prompts}
        self._refresh_prompt_list()
        self.status.SetLabel("Deleted custom prompt.")
        self._announce("Deleted custom prompt")

    def _on_use_prompt_clicked(self, _event: object) -> None:
        template = self.template_text.GetValue().strip()
        if not template:
            self.status.SetLabel("Prompt template is empty.")
            return
        rendered = self._render_prompt(template)
        if not rendered:
            self.status.SetLabel("Prompt rendered empty text.")
            return
        self._on_use_prompt(rendered)
        self._announce("Loaded prompt into Writing Assistant")
        self.dialog.EndModal(self._wx.ID_OK)

    def _on_preview_prompt(self, _event: object) -> None:
        self._render_preview()

    def _render_preview(self) -> None:
        template = self.template_text.GetValue().strip()
        if not template:
            self.preview.SetValue("")
            return
        unknown = unknown_template_variables(template)
        if unknown:
            self.status.SetLabel(f"Unknown variables: {', '.join(unknown)}")
            return
        rendered = self._render_prompt(template)
        self.preview.SetValue(rendered)
        variables = ", ".join(template_variables(template)) or "none"
        self.status.SetLabel(f"Preview rendered. Variables: {variables}.")

    def _render_prompt(self, template: str) -> str:
        return render_prompt_template(
            template,
            values={
                "selection": self._selection_text.strip(),
                "document": self._document_text.strip(),
                "tone": self.tone_text.GetValue().strip(),
                "audience": self.audience_text.GetValue().strip(),
                "goal": self.goal_text.GetValue().strip(),
            },
        )

    def _on_save_prompt(self, _event: object) -> None:
        key = self._selected_prompt_key
        if not key.startswith("custom:"):
            self.status.SetLabel("Built-in prompts cannot be overwritten.")
            return
        title = self.title_text.GetValue().strip()
        template = self.template_text.GetValue().strip()
        if not title:
            self.status.SetLabel("Title is required.")
            return
        if not template:
            self.status.SetLabel("Template is required.")
            return
        unknown = unknown_template_variables(template)
        if unknown:
            self.status.SetLabel(f"Unknown variables: {', '.join(unknown)}")
            return
        prompt_id = key.removeprefix("custom:")
        prompt = CustomPrompt(prompt_id=prompt_id, title=title, template=template)
        self._custom_prompts = upsert_custom_prompt(prompt)
        self._custom_by_id = {item.prompt_id: item for item in self._custom_prompts}
        self._refresh_prompt_list()
        self.status.SetLabel("Saved custom prompt.")
        self._announce("Saved custom prompt")


class AgentCenterDialog:
    def __init__(
        self,
        parent: object,
        *,
        selection_text: str,
        document_text: str,
        on_use_prompt: Callable[[str], None],
        announce: Callable[[str], None] | None = None,
    ) -> None:
        import wx

        self._wx = wx
        self._selection_text = selection_text
        self._document_text = document_text
        self._on_use_prompt = on_use_prompt
        self._announce = announce or (lambda _message: None)
        self._profiles = agent_profiles()

        self.dialog = wx.Dialog(
            parent,
            title="Agent Center",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((860, 620))

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "Choose a task-focused agent profile. Quill builds a draft prompt, then "
                    "you review and approve changes before applying."
                ),
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        self.agent_choice = wx.Choice(
            self.dialog,
            choices=[profile.title for profile in self._profiles],
        )
        self.agent_choice.SetSelection(0 if self._profiles else self._wx.NOT_FOUND)
        root.Add(self.agent_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.description = wx.StaticText(self.dialog, label="")
        root.Add(self.description, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self.dialog, label="Goal"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.goal_text = wx.TextCtrl(self.dialog)
        self.goal_text.SetValue("Help improve this draft.")
        row.Add(self.goal_text, 1, wx.RIGHT, 8)
        row.Add(wx.StaticText(self.dialog, label="Tone"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.tone_text = wx.TextCtrl(self.dialog)
        self.tone_text.SetValue("Clear and practical")
        row.Add(self.tone_text, 1)
        root.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(
            wx.StaticText(self.dialog, label="Audience"),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.RIGHT,
            8,
        )
        self.audience_text = wx.TextCtrl(self.dialog)
        self.audience_text.SetValue("General readers")
        row2.Add(self.audience_text, 1)
        root.Add(row2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.preview = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 260),
        )
        root.Add(self.preview, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.status = wx.StaticText(self.dialog, label="Ready.")
        root.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.generate_button = wx.Button(self.dialog, label="Generate Agent Prompt")
        self.use_button = wx.Button(self.dialog, label="Open in Writing Assistant")
        close_button = wx.Button(self.dialog, id=wx.ID_CANCEL, label="Close")
        buttons.Add(self.generate_button, 0, wx.RIGHT, 8)
        buttons.Add(self.use_button, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer(1)
        buttons.Add(close_button, 0)
        root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.dialog.SetSizer(root)

        self._current_prompt = ""
        self.agent_choice.Bind(wx.EVT_CHOICE, self._on_agent_changed)
        self.generate_button.Bind(wx.EVT_BUTTON, self._on_generate_prompt)
        self.use_button.Bind(wx.EVT_BUTTON, self._on_use_prompt_clicked)
        close_button.Bind(wx.EVT_BUTTON, lambda _e: self.dialog.EndModal(wx.ID_CANCEL))
        self._on_agent_changed(None)

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _on_agent_changed(self, _event: object | None) -> None:
        index = self.agent_choice.GetSelection()
        if index == self._wx.NOT_FOUND or index < 0 or index >= len(self._profiles):
            return
        profile = self._profiles[index]
        self.description.SetLabel(profile.description)
        self._on_generate_prompt(None)

    def _on_generate_prompt(self, _event: object | None) -> None:
        index = self.agent_choice.GetSelection()
        if index == self._wx.NOT_FOUND or index < 0 or index >= len(self._profiles):
            return
        profile = self._profiles[index]
        plan = build_agent_plan(
            profile.agent_id,
            selection_text=self._selection_text,
            document_text=self._document_text,
            goal=self.goal_text.GetValue(),
            audience=self.audience_text.GetValue(),
            tone=self.tone_text.GetValue(),
        )
        if plan is None:
            self.status.SetLabel("Could not build agent plan.")
            return
        checklist = "\n".join(f"- {item}" for item in plan.checks)
        self._current_prompt = plan.prompt
        self.preview.SetValue(f"{plan.prompt}\n\nSafety checks:\n{checklist}")
        self.status.SetLabel(f"Generated {plan.profile.title} prompt.")

    def _on_use_prompt_clicked(self, _event: object) -> None:
        if not self._current_prompt.strip():
            self._on_generate_prompt(None)
        if not self._current_prompt.strip():
            self.status.SetLabel("No prompt generated.")
            return
        self._use_prompt_callback(self._current_prompt)
        self._announce("Loaded agent prompt into Writing Assistant")
        self.dialog.EndModal(self._wx.ID_OK)


class WritingAssistantDialog:
    def __init__(
        self,
        parent: object,
        command_registry: CommandRegistry,
        feature_manager: FeatureManager | None,
        *,
        open_python_tool: Callable[[], None],
        selection_text: str = "",
        document_text: str = "",
        initial_prompt: str = "",
        assistant_enabled: bool = False,
        prompt_style: str = "balanced",
    ) -> None:
        import wx

        self._wx = wx
        self._registry = command_registry
        self._open_python_tool = open_python_tool
        self._selection_text = selection_text
        self._document_text = document_text
        self._assistant_enabled = assistant_enabled
        self._prompt_style = prompt_style
        self._all_tools = build_assistant_tools(command_registry, feature_manager)
        self._filtered_tools = list(self._all_tools)
        self._prompt_presets = assistant_prompt_presets()

        self.dialog = wx.Dialog(
            parent,
            title="Writing Assistant",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((960, 700))

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "Use the local command catalog to find writing actions quickly. "
                    "This shell is CPU-only and keeps tool actions accessible."
                ),
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        preset_row = wx.BoxSizer(wx.HORIZONTAL)
        self.preset_choice = wx.Choice(
            self.dialog,
            choices=[preset.title for preset in self._prompt_presets],
        )
        self.preset_choice.SetSelection(0 if self._prompt_presets else wx.NOT_FOUND)
        self.load_prompt_button = wx.Button(self.dialog, label="Load Prompt")
        self.use_selection_button = wx.Button(self.dialog, label="Use Selection")
        self.use_document_button = wx.Button(self.dialog, label="Use Document")
        preset_row.Add(
            wx.StaticText(self.dialog, label="Prompt presets"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        preset_row.AddSpacer(8)
        preset_row.Add(self.preset_choice, 1, wx.RIGHT, 8)
        preset_row.Add(self.load_prompt_button, 0, wx.RIGHT, 8)
        preset_row.Add(self.use_selection_button, 0, wx.RIGHT, 8)
        preset_row.Add(self.use_document_button, 0)
        root.Add(preset_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.prompt = wx.TextCtrl(self.dialog, style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB)
        self.prompt.SetHint("Describe the edit, review, or command you want")
        if initial_prompt.strip():
            self.prompt.SetValue(initial_prompt)
        elif self._prompt_presets:
            self.prompt.SetValue(
                render_assistant_prompt(
                    self._prompt_presets[0].name,
                    selection_text=self._selection_text,
                    document_text=self._document_text,
                )
            )
        root.Add(self.prompt, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.status = wx.StaticText(self.dialog, label="Showing all available tools.")
        root.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.chat_log = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 110),
        )
        self.chat_log.SetValue(self._initial_chat_log())
        root.Add(self.chat_log, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.results = wx.ListBox(self.dialog)
        root.Add(self.results, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.details = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 120),
        )
        root.Add(self.details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.suggest_button = wx.Button(self.dialog, label="Suggest")
        self.run_button = wx.Button(self.dialog, label="Run Selected Action")
        self.python_button = wx.Button(self.dialog, label="Run Python...")
        self.close_button = wx.Button(self.dialog, id=wx.ID_CANCEL, label="Close")
        buttons.Add(self.suggest_button, 0, wx.RIGHT, 8)
        buttons.Add(self.run_button, 0, wx.RIGHT, 8)
        buttons.Add(self.python_button, 0, wx.RIGHT, 8)
        buttons.AddStretchSpacer(1)
        buttons.Add(self.close_button, 0)
        root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.dialog.SetSizer(root)
        self.suggest_button.Bind(wx.EVT_BUTTON, self._on_suggest)
        self.run_button.Bind(wx.EVT_BUTTON, self._on_run_selected)
        self.python_button.Bind(wx.EVT_BUTTON, lambda _e: self._open_python_tool())
        self.close_button.Bind(wx.EVT_BUTTON, lambda _e: self.dialog.EndModal(wx.ID_CANCEL))
        self.results.Bind(wx.EVT_LISTBOX, self._on_selection_changed)
        self.results.Bind(wx.EVT_LISTBOX_DCLICK, self._on_run_selected)
        self.prompt.Bind(wx.EVT_TEXT, self._on_prompt_changed)
        self.load_prompt_button.Bind(wx.EVT_BUTTON, self._on_load_prompt)
        self.use_selection_button.Bind(wx.EVT_BUTTON, self._on_use_selection)
        self.use_document_button.Bind(wx.EVT_BUTTON, self._on_use_document)
        self.dialog.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

        self._refresh_results()

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _on_char_hook(self, event: object) -> None:
        key_code = event.GetKeyCode()
        if key_code == self._wx.WXK_ESCAPE:
            self.dialog.EndModal(self._wx.ID_CANCEL)
            return
        if key_code in (self._wx.WXK_RETURN, self._wx.WXK_NUMPAD_ENTER) and not event.ShiftDown():
            self._run_selected()
            return
        event.Skip()

    def _on_prompt_changed(self, _event: object) -> None:
        self._refresh_results()

    def _on_suggest(self, _event: object) -> None:
        self._refresh_results()

    def _initial_chat_log(self) -> str:
        lines = [
            "Chat log:",
            "- Use a preset to seed a prompt.",
            "- Run a command or Python transform, then apply the result back into the editor.",
        ]
        if self._assistant_enabled:
            lines.append(f"- Assistant prompts are enabled with the {self._prompt_style} style.")
        return "\n".join(lines)

    def _append_chat_log(self, line: str) -> None:
        current = self.chat_log.GetValue().rstrip()
        if current:
            current += "\n"
        self.chat_log.SetValue(f"{current}{line}".strip())

    def _on_load_prompt(self, _event: object) -> None:
        self._apply_prompt_from_preset()

    def _on_use_selection(self, _event: object) -> None:
        self.prompt.SetValue(self._selection_text.strip())
        self._append_chat_log("Loaded selection into the prompt.")

    def _on_use_document(self, _event: object) -> None:
        self.prompt.SetValue(self._document_text.strip())
        self._append_chat_log("Loaded document text into the prompt.")

    def _apply_prompt_from_preset(self) -> None:
        selected = self.preset_choice.GetSelection()
        if selected == self._wx.NOT_FOUND or selected < 0 or selected >= len(self._prompt_presets):
            return
        preset = self._prompt_presets[selected]
        prompt = render_assistant_prompt(
            preset.name,
            selection_text=self._selection_text,
            document_text=self._document_text,
        )
        self.prompt.SetValue(prompt)
        self._append_chat_log(f"Loaded preset: {preset.title}")

    def _refresh_results(self) -> None:
        query = self.prompt.GetValue()
        self._filtered_tools = rank_assistant_tools(query, self._all_tools, limit=50)
        labels: list[str] = []
        for tool in self._filtered_tools:
            suffix = f" [{tool.command_id}]" if tool.command_id else ""
            labels.append(f"{tool.title}{suffix}")
        self.results.Set(labels)
        if labels:
            self.results.SetSelection(0)
            self._update_details()
            self.status.SetLabel(f"{len(labels)} tool(s) matched.")
        else:
            self.details.SetValue("")
            self.status.SetLabel("No matching tools.")

    def _on_selection_changed(self, _event: object) -> None:
        self._update_details()

    def _update_details(self) -> None:
        selected = self.results.GetSelection()
        if selected == self._wx.NOT_FOUND:
            return
        if selected < 0 or selected >= len(self._filtered_tools):
            return
        tool = self._filtered_tools[selected]
        extra = ""
        if tool.command_id:
            extra = f"\nCommand: {tool.command_id}"
        self.details.SetValue(
            f"{tool.title}\n\n{tool.description}\n\nCategory: {tool.category}{extra}"
        )

    def _on_run_selected(self, _event: object) -> None:
        self._run_selected()

    def _run_selected(self) -> None:
        selected = self.results.GetSelection()
        if selected == self._wx.NOT_FOUND:
            return
        if selected < 0 or selected >= len(self._filtered_tools):
            return
        tool = self._filtered_tools[selected]
        if tool.command_id is None:
            if tool.name == "run_python":
                self._open_python_tool()
            return
        if tool.requires_confirmation:
            answer = self._wx.MessageBox(
                f"Run '{tool.title}' now?",
                "Confirm Assistant Action",
                style=self._wx.YES_NO | self._wx.ICON_WARNING,
            )
            if answer != self._wx.YES:
                return
        self._append_chat_log(f"Ran action: {tool.title}")
        self._registry.run(tool.command_id)
        self.dialog.EndModal(self._wx.ID_OK)


class SearchableModelPickerDialog:
    def __init__(self, parent: object, models: list[str]) -> None:
        import wx

        self._wx = wx
        self.dialog = wx.Dialog(
            parent,
            title="Available Models",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((640, 520))
        self._models = models
        self._filtered_models = list(models)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(wx.StaticText(self.dialog, label="Search models"), 0, wx.ALL, 8)
        self.query = wx.TextCtrl(self.dialog, style=wx.TE_PROCESS_ENTER)
        root.Add(self.query, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.listbox = wx.ListBox(self.dialog, choices=self._filtered_models)
        root.Add(self.listbox, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        buttons = self.dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
        self.dialog.SetSizer(root)

        self.query.Bind(wx.EVT_TEXT, self._on_query_changed)
        self.query.Bind(wx.EVT_TEXT_ENTER, self._on_query_enter)
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self._on_double_click)
        if self._filtered_models:
            self.listbox.SetSelection(0)
        self.query.SetFocus()

    def _on_query_changed(self, _event: object) -> None:
        query = self.query.GetValue()
        self._filtered_models = filter_model_names(self._models, query)
        self.listbox.Set(self._filtered_models)
        if self._filtered_models:
            self.listbox.SetSelection(0)

    def _on_query_enter(self, _event: object) -> None:
        if self._filtered_models:
            self.dialog.EndModal(self._wx.ID_OK)

    def _on_double_click(self, _event: object) -> None:
        self.dialog.EndModal(self._wx.ID_OK)

    def show_modal_and_get_selection(self) -> str:
        try:
            if self.dialog.ShowModal() != self._wx.ID_OK:
                return ""
            selection = self.listbox.GetSelection()
            if selection == self._wx.NOT_FOUND:
                return ""
            if selection < 0 or selection >= len(self._filtered_models):
                return ""
            return self._filtered_models[selection].strip()
        finally:
            self.dialog.Destroy()


class AIHubDialog:
    def __init__(
        self,
        parent: object,
        *,
        open_connection: Callable[[], None],
        open_model_settings: Callable[[], None],
        open_writing_assistant: Callable[[str], None],
        open_prompt_studio: Callable[[], None],
        open_agent_center: Callable[[], None],
        announce: Callable[[str], None] | None = None,
    ) -> None:
        import wx

        self._wx = wx
        self._open_connection = open_connection
        self._open_model_settings = open_model_settings
        self._open_writing_assistant = open_writing_assistant
        self._open_prompt_studio = open_prompt_studio
        self._open_agent_center = open_agent_center
        self._announce = announce or (lambda _message: None)
        self._settings = load_assistant_connection_settings()
        self._api_key = load_assistant_api_key()

        self.dialog = wx.Dialog(
            parent,
            title="AI Hub",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((760, 560))
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "AI Hub centralizes provider health, model selection, prompt workflows, "
                    "and agent entry points."
                ),
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        self.summary = wx.TextCtrl(
            self.dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_SIMPLE,
            size=(-1, 220),
        )
        root.Add(self.summary, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.status = wx.StaticText(self.dialog, label="Ready.")
        root.Add(self.status, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        actions = wx.GridSizer(rows=3, cols=3, hgap=8, vgap=8)
        self.verify_button = wx.Button(self.dialog, label="Verify Now")
        self.list_models_button = wx.Button(self.dialog, label="List Models")
        self.connection_button = wx.Button(self.dialog, label="Open Connection")
        self.model_button = wx.Button(self.dialog, label="Model Settings")
        self.prompt_button = wx.Button(self.dialog, label="Prompt Studio")
        self.agent_button = wx.Button(self.dialog, label="Agent Center")
        self.writing_button = wx.Button(self.dialog, label="Writing Assistant")
        actions.Add(self.verify_button, 0, wx.EXPAND)
        actions.Add(self.list_models_button, 0, wx.EXPAND)
        actions.Add(self.connection_button, 0, wx.EXPAND)
        actions.Add(self.model_button, 0, wx.EXPAND)
        actions.Add(self.prompt_button, 0, wx.EXPAND)
        actions.Add(self.agent_button, 0, wx.EXPAND)
        actions.Add(self.writing_button, 0, wx.EXPAND)
        actions.AddSpacer(0)
        actions.AddSpacer(0)
        root.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        close_row = wx.BoxSizer(wx.HORIZONTAL)
        close_row.AddStretchSpacer(1)
        close_row.Add(wx.Button(self.dialog, id=wx.ID_CLOSE, label="Close"), 0)
        root.Add(close_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.dialog.SetSizer(root)
        self.verify_button.Bind(wx.EVT_BUTTON, self._on_verify)
        self.list_models_button.Bind(wx.EVT_BUTTON, self._on_list_models)
        self.connection_button.Bind(wx.EVT_BUTTON, self._on_open_connection)
        self.model_button.Bind(wx.EVT_BUTTON, self._on_open_model)
        self.prompt_button.Bind(wx.EVT_BUTTON, self._on_open_prompt_studio)
        self.agent_button.Bind(wx.EVT_BUTTON, self._on_open_agent_center)
        self.writing_button.Bind(wx.EVT_BUTTON, self._on_open_writing_assistant)
        self.dialog.Bind(
            wx.EVT_BUTTON,
            lambda _e: self.dialog.EndModal(wx.ID_CLOSE),
            id=wx.ID_CLOSE,
        )
        self._refresh_summary()

    def show_modal(self) -> None:
        self.dialog.CentreOnParent()
        try:
            self.dialog.ShowModal()
        finally:
            self.dialog.Destroy()

    def _refresh_summary(self, verification: str = "Not checked") -> None:
        self._settings = load_assistant_connection_settings()
        provider = self._settings.provider or "off"
        host = self._settings.host or default_host_for_provider(provider)
        model = self._settings.model or default_model_for_provider(provider)
        requires_key = provider_requires_api_key(provider)
        key_state = "present" if bool(self._api_key.strip()) else "missing"
        guidance = "\n".join(
            f"- {item.model}: {item.framing} ({item.reason})"
            for item in recommended_model_guidance(provider)[:2]
        )
        summary = (
            f"Provider: {provider}\n"
            f"Host: {host or '(not required)'}\n"
            f"Model: {model or '(none)'}\n"
            f"API key required: {requires_key}\n"
            f"API key status: {key_state}\n"
            f"Verification: {verification}\n\n"
            "Recommended model guidance:\n"
            f"{guidance or '- No guidance available.'}\n\n"
            "Safety defaults:\n"
            "- Prompt and agent changes are review-first.\n"
            "- Destructive actions require explicit confirmation.\n"
            "- Cloud connections are user-configured and visible.\n"
            "- Chat transcripts are not persisted by default.\n"
            "- API keys use Credential Manager when available, with encrypted fallback."
        )
        self.summary.SetValue(summary)

    def _on_verify(self, _event: object) -> None:
        self._settings = load_assistant_connection_settings()
        self._api_key = load_assistant_api_key()
        ok, message = verify_assistant_connection(self._settings, self._api_key)
        self.status.SetLabel(message)
        self._refresh_summary(verification=message)
        self._announce(message)
        icon = self._wx.ICON_INFORMATION if ok else self._wx.ICON_WARNING
        self._wx.MessageBox(message, "AI Hub Verification", icon | self._wx.OK)

    def _on_list_models(self, _event: object) -> None:
        self._settings = load_assistant_connection_settings()
        self._api_key = load_assistant_api_key()
        models, error = list_assistant_models(self._settings, self._api_key)
        if error is not None:
            self.status.SetLabel(error)
            self._wx.MessageBox(error, "AI Hub Models", self._wx.ICON_WARNING | self._wx.OK)
            return
        if not models:
            message = "No models were returned by the endpoint."
            self.status.SetLabel(message)
            self._wx.MessageBox(message, "AI Hub Models", self._wx.ICON_INFORMATION | self._wx.OK)
            return
        picker = SearchableModelPickerDialog(self.dialog, models)
        selected = picker.show_modal_and_get_selection()
        if not selected:
            self.status.SetLabel("Model selection cancelled.")
            return
        self._settings.model = selected
        save_assistant_connection_settings(self._settings)
        self.status.SetLabel(f"Selected model: {selected}")
        self._refresh_summary(verification="Model updated from AI Hub")
        self._announce(f"Selected model {selected}")

    def _on_open_connection(self, _event: object) -> None:
        self._open_connection()
        self._api_key = load_assistant_api_key()
        self._refresh_summary(verification="Connection settings updated")

    def _on_open_model(self, _event: object) -> None:
        self._open_model_settings()
        self._refresh_summary(verification="Model settings opened")

    def _on_open_prompt_studio(self, _event: object) -> None:
        self._open_prompt_studio()
        self._refresh_summary(verification="Prompt Studio opened")

    def _on_open_agent_center(self, _event: object) -> None:
        self._open_agent_center()
        self._refresh_summary(verification="Agent Center opened")

    def _on_open_writing_assistant(self, _event: object) -> None:
        self._open_writing_assistant("")
        self._refresh_summary(verification="Writing Assistant opened")


class AssistantConnectionDialog:
    _PROVIDER_CHOICES: tuple[tuple[str, str], ...] = (
        ("off", "Off"),
        ("ollama", "Ollama (local)"),
        ("openai", "OpenAI"),
        ("claude", "Claude"),
        ("openrouter", "OpenRouter"),
        ("gemini", "Google Gemini"),
        ("azure_openai", "Microsoft Azure OpenAI"),
        ("ollama_cloud", "Ollama Cloud (API key)"),
        ("custom", "Custom OpenAI-compatible (advanced)"),
    )

    def __init__(self, parent: object) -> None:
        import wx

        self._wx = wx
        self.dialog = wx.Dialog(
            parent,
            title="AI Connection Settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize((780, 520))

        self._settings = load_assistant_connection_settings()
        self._api_key = load_assistant_api_key()
        self._api_key_revealed = False
        self.last_verification_ok: bool | None = None
        self.last_verification_message: str = "Not checked"

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(
            wx.StaticText(
                self.dialog,
                label=(
                    "Select a provider, verify connection, then list/filter models. "
                    "For supported cloud providers, default hosts are prefilled."
                ),
            ),
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        panel = wx.Panel(self.dialog)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        self.provider = wx.Choice(
            panel,
            choices=[label for _value, label in self._PROVIDER_CHOICES],
        )
        self.provider.SetSelection(self._provider_choice_index(self._settings.provider))
        panel_sizer.Add(
            wx.StaticText(panel, label="Provider"),
            0,
            wx.LEFT | wx.RIGHT | wx.TOP,
            8,
        )
        panel_sizer.Add(self.provider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.provider_hint = wx.StaticText(panel, label="")
        panel_sizer.Add(self.provider_hint, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.host = wx.TextCtrl(panel)
        self.host.SetValue(
            self._settings.host or default_host_for_provider(self._settings.provider)
        )
        panel_sizer.Add(wx.StaticText(panel, label="Host URL"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        panel_sizer.Add(self.host, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.model = wx.TextCtrl(panel)
        self.model.SetValue(self._settings.model)
        self.model.SetName("Model")
        panel_sizer.Add(wx.StaticText(panel, label="Model"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        panel_sizer.Add(self.model, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.api_key_label = wx.StaticText(
            panel,
            label="API key (optional; stored encrypted with DPAPI)",
        )
        panel_sizer.Add(self.api_key_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

        self.api_key_row = wx.BoxSizer(wx.HORIZONTAL)
        self.api_key = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        self.api_key.SetValue(self._api_key)
        self.api_key.SetName("API key")
        self.api_key_row.Add(self.api_key, 1, wx.EXPAND | wx.RIGHT, 8)
        self.reveal_api_key = wx.Button(panel, label="Reveal")
        self.reveal_api_key.SetName("Reveal API key")
        self.api_key_row.Add(self.reveal_api_key, 0)
        panel_sizer.Add(self.api_key_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        self.verify_button = wx.Button(panel, label="Verify Connection")
        self.list_models_button = wx.Button(panel, label="List Models")
        self.recommend_button = wx.Button(panel, label="Recommend Model")
        actions.Add(self.verify_button, 0, wx.RIGHT, 8)
        actions.Add(self.list_models_button, 0, wx.RIGHT, 8)
        actions.Add(self.recommend_button, 0)
        panel_sizer.Add(actions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.connection_status = wx.StaticText(
            panel,
            label=(
                "Tip: Verify first, then List Models and search to quickly pick the best model."
            ),
        )
        panel_sizer.Add(self.connection_status, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        panel.SetSizer(panel_sizer)
        root.Add(panel, 1, wx.EXPAND | wx.ALL, 8)

        buttons = self.dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            root.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)
        self.dialog.SetSizerAndFit(root)
        self.provider.Bind(wx.EVT_CHOICE, self._on_provider_changed)
        self.verify_button.Bind(wx.EVT_BUTTON, self._on_verify_connection)
        self.list_models_button.Bind(wx.EVT_BUTTON, self._on_list_models)
        self.recommend_button.Bind(wx.EVT_BUTTON, self._on_recommend_model)
        self.reveal_api_key.Bind(wx.EVT_BUTTON, self._on_toggle_api_key_reveal)
        self._on_provider_changed(None)

    def _provider_choice_index(self, provider: str) -> int:
        normalized = provider.strip().lower()
        for index, (value, _label) in enumerate(self._PROVIDER_CHOICES):
            if value == normalized:
                return index
        return 1

    def _provider_value(self) -> str:
        selection = self.provider.GetSelection()
        if selection < 0 or selection >= len(self._PROVIDER_CHOICES):
            return "ollama"
        return self._PROVIDER_CHOICES[selection][0]

    def _current_settings(self) -> AssistantConnectionSettings:
        provider = self._provider_value()
        fallback_host = default_host_for_provider(provider)
        fallback_model = default_model_for_provider(provider)
        return AssistantConnectionSettings(
            provider=provider,
            host=self.host.GetValue().strip() or fallback_host,
            model=self.model.GetValue().strip() or fallback_model,
        )

    def _on_provider_changed(self, _event: object | None) -> None:
        provider = self._provider_value()
        host_value = self.host.GetValue().strip()
        known_hosts = {
            default_host_for_provider(name)
            for name, _label in self._PROVIDER_CHOICES
            if default_host_for_provider(name)
        }
        if not host_value or host_value in known_hosts:
            self.host.SetValue(default_host_for_provider(provider))
        model_value = self.model.GetValue().strip()
        known_models = {
            default_model_for_provider(name) for name, _label in self._PROVIDER_CHOICES
        }
        if not model_value or model_value in known_models:
            self.model.SetValue(default_model_for_provider(provider))
        requires_key = provider_requires_api_key(provider)
        self.api_key_label.SetLabel(provider_api_key_label(provider))
        self.provider_hint.SetLabel(provider_help_text(provider))
        self.api_key.Enable(requires_key)
        self.reveal_api_key.Enable(requires_key)
        if not requires_key and self._api_key_revealed:
            self._set_api_key_revealed(False)
        self.dialog.Layout()

    def _on_toggle_api_key_reveal(self, _event: object) -> None:
        self._set_api_key_revealed(not self._api_key_revealed)

    def _set_api_key_revealed(self, revealed: bool) -> None:
        value = self.api_key.GetValue()
        parent = self.api_key.GetParent()
        self.api_key_row.Detach(self.api_key)
        self.api_key.Destroy()
        style = 0 if revealed else self._wx.TE_PASSWORD
        self.api_key = self._wx.TextCtrl(parent, style=style)
        self.api_key.SetValue(value)
        self.api_key.SetName("API key")
        self.api_key_row.Insert(0, self.api_key, 1, self._wx.EXPAND | self._wx.RIGHT, 8)
        self._api_key_revealed = revealed
        self.reveal_api_key.SetLabel("Hide" if revealed else "Reveal")
        self.reveal_api_key.SetName("Hide API key" if revealed else "Reveal API key")
        self.dialog.Layout()

    def _on_verify_connection(self, _event: object) -> None:
        settings = self._current_settings()
        ok, message = verify_assistant_connection(settings, self.api_key.GetValue())
        self.connection_status.SetLabel(message)
        icon = self._wx.ICON_INFORMATION if ok else self._wx.ICON_WARNING
        self._wx.MessageBox(message, "AI Connection Check", icon | self._wx.OK)

    def _on_list_models(self, _event: object) -> None:
        settings = self._current_settings()
        models, error = list_assistant_models(settings, self.api_key.GetValue())
        if error is not None:
            self.connection_status.SetLabel(error)
            self._wx.MessageBox(error, "Model Discovery", self._wx.ICON_WARNING | self._wx.OK)
            return
        if not models:
            message = "Connection succeeded, but the endpoint returned no models."
            self.connection_status.SetLabel(message)
            self._wx.MessageBox(message, "Model Discovery", self._wx.ICON_INFORMATION | self._wx.OK)
            return

        picker = SearchableModelPickerDialog(self.dialog, models)
        selected = picker.show_modal_and_get_selection()
        if selected:
            self.model.SetValue(selected)
            self.connection_status.SetLabel(f"Selected model: {selected}")
        else:
            self.connection_status.SetLabel("Model selection cancelled.")

    def _on_recommend_model(self, _event: object) -> None:
        settings = self._current_settings()
        recommendations = recommended_model_guidance(settings.provider)
        if not recommendations:
            self.connection_status.SetLabel("No model recommendations available.")
            return
        labels = [f"{item.model} - {item.framing}: {item.reason}" for item in recommendations]
        picker = self._wx.SingleChoiceDialog(
            self.dialog,
            "Choose a recommended model profile:",
            "Model Recommendations",
            labels,
        )
        try:
            if picker.ShowModal() != self._wx.ID_OK:
                self.connection_status.SetLabel("Recommendation selection cancelled.")
                return
            selected_index = picker.GetSelection()
        finally:
            picker.Destroy()
        if selected_index < 0 or selected_index >= len(recommendations):
            self.connection_status.SetLabel("Recommendation selection cancelled.")
            return
        selected: ModelRecommendation = recommendations[selected_index]
        self.model.SetValue(selected.model)
        self.connection_status.SetLabel(
            f"Recommended model selected: {selected.model} ({selected.framing})"
        )

    def show_modal(self) -> bool:
        self.dialog.CentreOnParent()
        try:
            if self.dialog.ShowModal() != self._wx.ID_OK:
                return False
            settings = self._current_settings()
            api_key = self.api_key.GetValue()
            save_assistant_connection_settings(settings)
            save_assistant_api_key(api_key)
            ok, message = verify_assistant_connection(settings, api_key)
            self.last_verification_ok = ok
            self.last_verification_message = message
            self.connection_status.SetLabel(message)
            return True
        finally:
            self.dialog.Destroy()
