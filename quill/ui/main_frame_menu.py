"""Menu-bar construction for ``MainFrame`` (CQ-1).

Extracted verbatim from ``main_frame.py`` into a cohesive mixin so the UI
monolith shrinks without any behaviour change. ``MainFrame`` inherits
``MenuBuilderMixin`` and ``_build_menu`` resolves identically through the MRO.
The method is fully self-contained: it reads ``wx`` from ``self._wx`` and
reaches every menu id, submenu, label helper, and refresh routine through
``self``, so no module-level imports are required here.
"""

from __future__ import annotations


class MenuBuilderMixin:
    def _build_menu(self) -> None:
        wx = self._wx
        menu_bar = wx.MenuBar()

        self._id_new = wx.ID_NEW
        self._id_open = wx.ID_OPEN
        self._id_save = wx.ID_SAVE
        self._id_save_as = wx.ID_SAVEAS
        self._id_exit = wx.ID_EXIT
        self._id_palette = wx.NewIdRef()
        self._id_preferences = wx.NewIdRef()
        self._id_menu_editor = wx.NewIdRef()
        self._id_open_url = wx.NewIdRef()
        self._id_close_document = wx.NewIdRef()
        self._id_save_all = wx.NewIdRef()
        self._id_reload_from_disk = wx.NewIdRef()
        self._id_restore_backup = wx.NewIdRef()
        self._id_save_session = wx.NewIdRef()
        self._id_open_session = wx.NewIdRef()
        self._id_clear_recent_sessions = wx.NewIdRef()
        self._id_page_setup = wx.NewIdRef()
        self._id_print = wx.NewIdRef()
        self._id_save_plain_text = wx.NewIdRef()
        self._id_clear_recent = wx.NewIdRef()
        self._sessions_menu = wx.Menu()
        self._open_documents_menu = wx.Menu()
        self._recent_sessions_menu = wx.Menu()

        file_menu = wx.Menu()
        # --- Create / open ---
        file_menu.Append(self._id_new, self._menu_label("&New", "file.new"))
        file_menu.Append(self._id_open, self._menu_label("&Open...", "file.open"))
        self._recent_menu = wx.Menu()
        file_menu.AppendSubMenu(self._recent_menu, "Open &Recent")
        self._refresh_recent_menu()
        file_menu.Append(self._id_open_url, "Open from &URL...")
        file_menu.AppendSubMenu(self._sessions_menu, "&Workspace Snapshots")
        file_menu.AppendSeparator()
        # --- Save ---
        file_menu.Append(self._id_save, self._menu_label("&Save", "file.save"))
        file_menu.Append(self._id_save_as, self._menu_label("Save &As...", "file.save_as"))
        file_menu.Append(self._id_save_all, "Save A&ll")
        file_menu.Append(self._id_save_plain_text, "Save As Plain &Text...")
        file_menu.AppendSeparator()
        # --- Restore / reload ---
        file_menu.Append(self._id_reload_from_disk, "&Reload from Disk")
        file_menu.Append(self._id_restore_backup, "Restore &Backup...")
        file_menu.AppendSeparator()
        # --- Print ---
        file_menu.Append(self._id_page_setup, "Pa&ge Setup...")
        file_menu.Append(self._id_print, self._menu_label("&Print...", "file.print"))
        file_menu.AppendSeparator()
        # --- Close ---
        file_menu.Append(
            self._id_close_document,
            self._menu_label("&Close Document", "file.close_document"),
        )
        file_menu.Append(self._id_exit, self._menu_label("E&xit", "app.exit"))
        menu_bar.Append(file_menu, "&File")

        self._id_find = wx.NewIdRef()
        self._id_undo = wx.NewIdRef()
        self._id_redo = wx.NewIdRef()
        self._id_copy_with_source = wx.NewIdRef()
        self._id_toggle_extend_selection_mode = wx.NewIdRef()
        self._id_replace = wx.NewIdRef()
        self._id_replace_all = wx.NewIdRef()
        self._id_find_next = wx.NewIdRef()
        self._id_find_previous = wx.NewIdRef()
        self._id_find_all_matches = wx.NewIdRef()
        self._id_search_in_files = wx.NewIdRef()
        self._id_replace_in_files = wx.NewIdRef()
        self._id_insert_link = wx.NewIdRef()
        self._id_follow_link = wx.NewIdRef()
        self._id_word_prediction = wx.NewIdRef()
        self._id_select_line = wx.NewIdRef()
        self._id_select_paragraph = wx.NewIdRef()
        self._id_select_block = wx.NewIdRef()
        self._id_select_to_start_of_line = wx.NewIdRef()
        self._id_select_to_end_of_line = wx.NewIdRef()
        self._id_select_to_start_of_document = wx.NewIdRef()
        self._id_select_to_end_of_document = wx.NewIdRef()
        self._id_set_mark = wx.NewIdRef()
        self._id_pop_mark = wx.NewIdRef()
        self._id_exchange_point_mark = wx.NewIdRef()
        self._id_list_marks = wx.NewIdRef()
        self._id_sort_lines_ascending = wx.NewIdRef()
        self._id_sort_lines_descending = wx.NewIdRef()
        self._id_reverse_lines = wx.NewIdRef()
        self._id_remove_duplicate_lines = wx.NewIdRef()
        self._id_trim_trailing_whitespace = wx.NewIdRef()
        self._id_normalize_whitespace = wx.NewIdRef()
        self._id_convert_indentation_to_spaces = wx.NewIdRef()
        self._id_convert_indentation_to_tabs = wx.NewIdRef()
        edit_menu = wx.Menu()
        edit_menu.Append(self._id_undo, self._menu_label("&Undo", "edit.undo"))
        edit_menu.Append(self._id_redo, self._menu_label("&Redo", "edit.redo"))
        edit_menu.AppendSeparator()
        # Standard clipboard items. wxTextCtrl routes these IDs natively, so
        # we don't need to bind handlers; the active editor handles them.
        edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X")
        edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C")
        edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V")
        edit_menu.Append(
            self._id_copy_with_source,
            self._menu_label("Copy With &Source", "edit.copy_with_source"),
        )
        edit_menu.AppendSeparator()
        edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        # Selection submenu (detailed selection operations + mark ring)
        # is populated later in this method and appended here.
        edit_menu.AppendCheckItem(
            self._id_toggle_extend_selection_mode,
            self._menu_label(
                "E&xtend Selection Mode",
                "edit.toggle_extend_selection_mode",
            ),
        )
        edit_menu.Check(self._id_toggle_extend_selection_mode, self._extend_selection_mode)
        edit_menu.AppendSeparator()
        # Insert Link lives in the Insert menu (its primary home); the Edit menu
        # keeps only Follow Link so the same command is not duplicated (MENU-3).
        edit_menu.Append(
            self._id_follow_link,
            self._menu_label("&Follow Link", "edit.follow_link"),
        )
        edit_menu.Append(
            self._id_word_prediction,
            self._menu_label("&Word Prediction...", "edit.word_prediction"),
        )
        edit_menu.AppendSeparator()
        selection_menu = wx.Menu()
        selection_menu.Append(
            self._id_select_line,
            self._menu_label("Select &Line", "edit.select_line"),
        )
        selection_menu.Append(
            self._id_select_paragraph,
            self._menu_label("Select &Paragraph", "edit.select_paragraph"),
        )
        selection_menu.Append(
            self._id_select_block,
            self._menu_label("Select &Block", "edit.select_block"),
        )
        selection_menu.AppendSeparator()
        selection_menu.Append(
            self._id_select_to_end_of_line,
            self._menu_label("Select to End of &Line", "edit.select_to_end_of_line"),
        )
        selection_menu.Append(
            self._id_select_to_start_of_line,
            self._menu_label(
                "Select to Start of Li&ne",
                "edit.select_to_start_of_line",
            ),
        )
        selection_menu.Append(
            self._id_select_to_end_of_document,
            self._menu_label(
                "Select to End of &Document",
                "edit.select_to_end_of_document",
            ),
        )
        selection_menu.Append(
            self._id_select_to_start_of_document,
            self._menu_label(
                "Select to Start of D&ocument",
                "edit.select_to_start_of_document",
            ),
        )
        mark_ring_menu = wx.Menu()
        mark_ring_menu.Append(
            self._id_set_mark,
            self._menu_label("&Set Temporary Mark", "edit.set_mark"),
        )
        mark_ring_menu.Append(
            self._id_pop_mark,
            self._menu_label("&Jump to Previous Mark", "edit.pop_mark"),
        )
        mark_ring_menu.Append(
            self._id_exchange_point_mark,
            self._menu_label(
                "&Swap Cursor and Mark",
                "edit.exchange_point_mark",
            ),
        )
        mark_ring_menu.Append(
            self._id_list_marks,
            self._menu_label("&List Recent Marks", "edit.list_marks"),
        )
        selection_menu.AppendSeparator()
        selection_menu.AppendSubMenu(mark_ring_menu, "Recent &Marks (Ring)")
        edit_menu.AppendSubMenu(selection_menu, "&Selection")
        menu_bar.Append(edit_menu, "&Edit")
        insert_menu = wx.Menu()
        menu_bar.Append(insert_menu, "&Insert")

        search_menu = wx.Menu()
        search_menu.Append(self._id_find, self._menu_label("&Find...", "edit.find"))
        search_menu.Append(
            self._id_replace,
            self._menu_label("&Replace...", "edit.replace"),
        )
        search_menu.AppendSeparator()
        search_menu.Append(
            self._id_find_next,
            self._menu_label("Find &Next", "edit.find_next"),
        )
        search_menu.Append(
            self._id_find_previous,
            self._menu_label("Find &Previous", "edit.find_previous"),
        )
        search_menu.Append(
            self._id_find_all_matches,
            self._menu_label("Find &All Matches", "edit.find_all_matches"),
        )
        search_menu.AppendSeparator()
        search_menu.Append(
            self._id_search_in_files,
            self._menu_label("Search in &Files...", "tools.search_in_files"),
        )
        search_menu.Append(
            self._id_replace_in_files,
            self._menu_label("&Replace Across Files...", "tools.replace_in_files"),
        )
        self._id_send_to_tray = wx.NewIdRef()
        self._id_toggle_tray_mode = wx.NewIdRef()
        self._id_toggle_soft_wrap = wx.NewIdRef()
        self._id_toggle_tab_control = wx.NewIdRef()
        self._id_toggle_find_wrap = wx.NewIdRef()
        self._id_toggle_title_full_path = wx.NewIdRef()
        self._id_toggle_auto_check_updates = wx.NewIdRef()
        self._id_toggle_dark_mode = wx.NewIdRef()
        self._id_toggle_persistent_undo = wx.NewIdRef()
        self._id_toggle_spellcheck_as_you_type = wx.NewIdRef()
        self._id_toggle_intellisense_as_you_type = wx.NewIdRef()
        self._id_browser_preview = wx.NewIdRef()
        self._id_preview = wx.NewIdRef()
        self._id_split_preview = wx.NewIdRef()
        self._id_focus_preview = wx.NewIdRef()
        self._id_toggle_auto_side_preview = wx.NewIdRef()
        self._id_start_with_no_document_open = wx.NewIdRef()
        self._id_dirty_title_text = wx.NewIdRef()
        self._id_dirty_title_asterisk = wx.NewIdRef()
        self._id_dirty_title_asterisk_text = wx.NewIdRef()
        view_menu = wx.Menu()
        view_menu.AppendCheckItem(self._id_toggle_tray_mode, "Enable System Tray &Mode")
        view_menu.Check(self._id_toggle_tray_mode, self.settings.tray_enabled)
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(
            self._id_toggle_soft_wrap,
            self._menu_label("Toggle Soft &Wrap", "view.toggle_soft_wrap"),
        )
        view_menu.Check(self._id_toggle_soft_wrap, self.settings.soft_wrap)
        view_menu.AppendCheckItem(self._id_toggle_auto_side_preview, "&Auto Side-by-Side Preview")
        view_menu.Check(self._id_toggle_auto_side_preview, self.settings.auto_side_preview)
        view_menu.AppendCheckItem(self._id_toggle_tab_control, "Show &Tab Control")
        view_menu.Check(self._id_toggle_tab_control, self.settings.show_tab_control)
        view_menu.AppendCheckItem(self._id_toggle_find_wrap, "Wrap &Find Searches")
        view_menu.Check(self._id_toggle_find_wrap, self.settings.wrap_find)
        view_menu.AppendCheckItem(self._id_toggle_title_full_path, "Show Full Path in &Title Bar")
        view_menu.Check(
            self._id_toggle_title_full_path,
            getattr(self.settings, "title_bar_path_mode", "name") == "full_path",
        )
        dirty_menu = wx.Menu()
        dirty_menu.AppendRadioItem(self._id_dirty_title_text, "Dirty Indicator: Text")
        dirty_menu.AppendRadioItem(self._id_dirty_title_asterisk, "Dirty Indicator: Asterisk")
        dirty_menu.AppendRadioItem(
            self._id_dirty_title_asterisk_text,
            "Dirty Indicator: Asterisk + Text",
        )
        dirty_style = getattr(self.settings, "dirty_title_style", "text")
        dirty_menu.Check(self._id_dirty_title_text, dirty_style == "text")
        dirty_menu.Check(self._id_dirty_title_asterisk, dirty_style == "asterisk")
        dirty_menu.Check(
            self._id_dirty_title_asterisk_text,
            dirty_style == "asterisk_text",
        )
        view_menu.AppendSubMenu(dirty_menu, "&Dirty Title Style")
        view_menu.AppendCheckItem(self._id_toggle_dark_mode, "Toggle &Dark Mode")
        view_menu.Check(self._id_toggle_dark_mode, self.settings.theme == "dark")
        view_menu.AppendCheckItem(
            self._id_toggle_persistent_undo,
            "Enable &Persistent Undo",
        )
        view_menu.Check(self._id_toggle_persistent_undo, self.settings.persistent_undo)
        view_menu.AppendCheckItem(
            self._id_toggle_spellcheck_as_you_type,
            "Spell Check As You &Type",
        )
        view_menu.Check(
            self._id_toggle_spellcheck_as_you_type,
            self.settings.spellcheck_as_you_type,
        )
        view_menu.AppendCheckItem(
            self._id_toggle_intellisense_as_you_type,
            "Word Prediction As You &Type",
        )
        view_menu.Check(
            self._id_toggle_intellisense_as_you_type,
            getattr(self.settings, "intellisense_as_you_type", False),
        )
        view_menu.AppendCheckItem(
            self._id_start_with_no_document_open,
            "Start With &No Document Open",
        )
        view_menu.Check(
            self._id_start_with_no_document_open,
            self.settings.start_with_no_document_open,
        )
        view_menu.Append(
            self._id_preview,
            self._menu_label("&Preview...", "view.preview"),
        )
        view_menu.Append(
            self._id_split_preview,
            self._menu_label("Preview &Side by Side", "view.split_preview"),
        )
        view_menu.Append(
            self._id_focus_preview,
            self._menu_label("&Focus Preview", "view.focus_preview"),
        )
        view_menu.Append(
            self._id_browser_preview,
            self._menu_label("&Browser Preview...", "view.browser_preview"),
        )
        menu_bar.Append(view_menu, "&View")
        menu_bar.Append(search_menu, "&Search")

        navigate_menu = wx.Menu()
        self._id_go_to_line = wx.NewIdRef()
        self._id_set_bookmark = wx.NewIdRef()
        self._id_go_to_bookmark = wx.NewIdRef()
        self._id_list_bookmarks = wx.NewIdRef()
        self._id_go_to_page = wx.NewIdRef()
        self._id_back_location = wx.NewIdRef()
        self._id_forward_location = wx.NewIdRef()
        self._id_next_heading = wx.NewIdRef()
        self._id_previous_heading = wx.NewIdRef()
        self._id_next_block = wx.NewIdRef()
        self._id_previous_block = wx.NewIdRef()
        self._id_outline_navigator = wx.NewIdRef()
        self._id_heading_organizer = wx.NewIdRef()
        self._id_match_bracket = wx.NewIdRef()
        self._id_next_structure = wx.NewIdRef()
        self._id_previous_structure = wx.NewIdRef()
        self._id_next_region = wx.NewIdRef()
        self._id_previous_region = wx.NewIdRef()
        navigate_menu.Append(
            self._id_go_to_line,
            self._menu_label("&Go To Line...", "navigate.go_to_line"),
        )
        navigate_menu.Append(
            self._id_go_to_page,
            self._menu_label("Go To &Page...", "navigate.go_to_page"),
        )
        navigate_menu.Append(
            self._id_back_location,
            self._menu_label("&Back Location", "navigate.back_location"),
        )
        navigate_menu.Append(
            self._id_forward_location,
            self._menu_label("&Forward Location", "navigate.forward_location"),
        )
        navigate_menu.Append(
            self._id_next_heading,
            self._menu_label("Next &Heading", "navigate.next_heading"),
        )
        navigate_menu.Append(
            self._id_previous_heading,
            self._menu_label("Pre&vious Heading", "navigate.previous_heading"),
        )
        navigate_menu.Append(
            self._id_next_block,
            self._menu_label("Next &Block", "navigate.next_block"),
        )
        navigate_menu.Append(
            self._id_previous_block,
            self._menu_label("Previous Bl&ock", "navigate.previous_block"),
        )
        navigate_menu.Append(
            self._id_outline_navigator,
            self._menu_label("Outline &Navigator...", "navigate.outline_navigator"),
        )
        navigate_menu.Append(
            self._id_heading_organizer,
            self._menu_label("&Heading Organizer...", "navigate.heading_organizer"),
        )
        navigate_menu.Append(
            self._id_match_bracket,
            self._menu_label("Match &Bracket", "navigate.match_bracket"),
        )
        navigate_menu.Append(
            self._id_next_structure,
            self._menu_label("Next Str&ucture", "navigate.next_structure"),
        )
        navigate_menu.Append(
            self._id_previous_structure,
            self._menu_label("Previous Structu&re", "navigate.previous_structure"),
        )
        navigate_menu.Append(
            self._id_next_region,
            self._menu_label("Next Re&gion", "navigate.next_region"),
        )
        navigate_menu.Append(
            self._id_previous_region,
            self._menu_label("Previous Regio&n", "navigate.previous_region"),
        )
        navigate_menu.AppendSeparator()
        navigate_menu.Append(
            self._id_set_bookmark,
            self._menu_label("Set &Bookmark...", "navigate.set_bookmark"),
        )
        navigate_menu.Append(
            self._id_go_to_bookmark,
            self._menu_label("Go To &Bookmark...", "navigate.go_to_bookmark"),
        )
        navigate_menu.Append(
            self._id_list_bookmarks,
            self._menu_label("List B&ookmarks...", "navigate.list_bookmarks"),
        )
        self._id_insert_html_tag = wx.NewIdRef()
        self._id_insert_markdown_tag = wx.NewIdRef()
        self._id_insert_snippet = wx.NewIdRef()
        self._id_manage_snippets = wx.NewIdRef()
        self._id_format_bold = wx.NewIdRef()
        self._id_format_italic = wx.NewIdRef()
        self._id_heading_1 = wx.NewIdRef()
        self._id_heading_2 = wx.NewIdRef()
        self._id_heading_3 = wx.NewIdRef()
        self._id_heading_4 = wx.NewIdRef()
        self._id_heading_5 = wx.NewIdRef()
        self._id_heading_6 = wx.NewIdRef()
        self._id_decrease_heading_level = wx.NewIdRef()
        self._id_increase_heading_level = wx.NewIdRef()
        self._id_style_headings = wx.NewIdRef()
        self._id_upper_case = wx.NewIdRef()
        self._id_lower_case = wx.NewIdRef()
        self._id_title_case = wx.NewIdRef()
        self._id_sentence_case = wx.NewIdRef()
        self._id_toggle_case = wx.NewIdRef()
        self._id_toggle_line_comment = wx.NewIdRef()
        self._id_toggle_block_comment = wx.NewIdRef()
        self._id_indent = wx.NewIdRef()
        self._id_outdent = wx.NewIdRef()
        self._id_move_line_up = wx.NewIdRef()
        self._id_move_line_down = wx.NewIdRef()
        self._id_duplicate_line = wx.NewIdRef()
        self._id_delete_line = wx.NewIdRef()
        self._id_join_lines = wx.NewIdRef()
        self._id_insert_bullet_list = wx.NewIdRef()
        self._id_insert_numbered_list = wx.NewIdRef()
        self._id_insert_task_list = wx.NewIdRef()
        self._id_open_list_manager = wx.NewIdRef()
        self._id_insert_code_block = wx.NewIdRef()
        self._id_insert_footnote = wx.NewIdRef()
        self._id_insert_table = wx.NewIdRef()
        format_menu = wx.Menu()
        case_menu = wx.Menu()
        case_menu.Append(
            self._id_upper_case,
            self._menu_label("&Upper Case", "format.upper_case"),
        )
        case_menu.Append(
            self._id_lower_case,
            self._menu_label("&Lower Case", "format.lower_case"),
        )
        case_menu.Append(
            self._id_title_case,
            self._menu_label("&Title Case", "format.title_case"),
        )
        case_menu.Append(
            self._id_sentence_case,
            self._menu_label("&Sentence Case", "format.sentence_case"),
        )
        case_menu.Append(
            self._id_toggle_case,
            self._menu_label("To&ggle Case", "format.toggle_case"),
        )
        format_menu.AppendSubMenu(case_menu, "Change &Case")
        format_menu.AppendSeparator()
        format_menu.Append(
            self._id_toggle_line_comment,
            self._menu_label(
                "Toggle Line &Comment",
                "format.toggle_line_comment",
            ),
        )
        format_menu.Append(
            self._id_toggle_block_comment,
            self._menu_label(
                "Toggle &Block Comment",
                "format.toggle_block_comment",
            ),
        )
        format_menu.Append(
            self._id_indent,
            self._menu_label("&Indent", "format.indent"),
        )
        format_menu.Append(
            self._id_outdent,
            self._menu_label("O&utdent", "format.outdent"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(
            self._id_move_line_up,
            self._menu_label("Move Line &Up", "format.move_line_up"),
        )
        format_menu.Append(
            self._id_move_line_down,
            self._menu_label("Move Line &Down", "format.move_line_down"),
        )
        format_menu.Append(
            self._id_duplicate_line,
            self._menu_label("&Duplicate Line", "format.duplicate_line"),
        )
        format_menu.Append(
            self._id_delete_line,
            self._menu_label("&Delete Line", "format.delete_line"),
        )
        format_menu.Append(
            self._id_join_lines,
            self._menu_label("&Join Lines", "format.join_lines"),
        )
        format_menu.AppendSeparator()
        format_menu.Append(self._id_format_bold, self._menu_label("&Bold", "format.bold"))
        format_menu.Append(self._id_format_italic, self._menu_label("&Italic", "format.italic"))
        heading_menu = wx.Menu()
        heading_menu.Append(self._id_heading_1, self._menu_label("Heading &1", "format.heading_1"))
        heading_menu.Append(self._id_heading_2, self._menu_label("Heading &2", "format.heading_2"))
        heading_menu.Append(self._id_heading_3, self._menu_label("Heading &3", "format.heading_3"))
        heading_menu.Append(self._id_heading_4, self._menu_label("Heading &4", "format.heading_4"))
        heading_menu.Append(self._id_heading_5, self._menu_label("Heading &5", "format.heading_5"))
        heading_menu.Append(self._id_heading_6, self._menu_label("Heading &6", "format.heading_6"))
        heading_menu.AppendSeparator()
        heading_menu.Append(
            self._id_decrease_heading_level,
            self._menu_label(
                "Decrease Level",
                "format.decrease_heading_level",
            ),
        )
        heading_menu.Append(
            self._id_increase_heading_level,
            self._menu_label(
                "Increase Level",
                "format.increase_heading_level",
            ),
        )
        heading_menu.AppendSeparator()
        heading_menu.Append(
            self._id_style_headings,
            self._menu_label("&Style Headings...", "format.style_headings"),
        )
        insert_menu.Append(
            self._id_insert_link,
            self._menu_label("Insert &Link...", "edit.insert_link"),
        )
        insert_menu.AppendSeparator()
        insert_menu.AppendSubMenu(heading_menu, "&Heading")
        list_menu = wx.Menu()
        list_menu.Append(
            self._id_insert_bullet_list,
            self._menu_label("B&ullet", "format.insert_bullet_list"),
        )
        list_menu.Append(
            self._id_insert_numbered_list,
            self._menu_label("&Numbered", "format.insert_numbered_list"),
        )
        list_menu.Append(
            self._id_insert_task_list,
            self._menu_label("&Task", "format.insert_task_list"),
        )
        list_menu.AppendSeparator()
        list_menu.Append(
            self._id_open_list_manager,
            self._menu_label("List &Manager...", "format.list_manager"),
        )
        insert_menu.AppendSubMenu(list_menu, "&List")
        insert_menu.Append(
            self._id_insert_code_block,
            self._menu_label("Insert Code &Block", "format.insert_code_block"),
        )
        insert_menu.Append(
            self._id_insert_footnote,
            self._menu_label("Insert &Footnote", "format.insert_footnote"),
        )
        insert_menu.Append(
            self._id_insert_table,
            self._menu_label("Insert &Table...", "format.insert_table"),
        )
        insert_menu.AppendSeparator()
        insert_menu.Append(
            self._id_insert_html_tag,
            self._menu_label("Insert &HTML Tag...", "format.insert_html_tag"),
        )
        insert_menu.Append(
            self._id_insert_markdown_tag,
            self._menu_label("Insert &Markdown Tag...", "format.insert_markdown_tag"),
        )
        insert_menu.Append(
            self._id_insert_snippet,
            self._menu_label("Insert S&nippet...", "format.insert_snippet"),
        )
        insert_menu.Append(
            self._id_manage_snippets,
            self._menu_label("Manage Snippets...", "format.manage_snippets"),
        )
        self._id_next_document = wx.NewIdRef()
        self._id_previous_document = wx.NewIdRef()
        window_menu = wx.Menu()
        window_menu.Append(
            self._id_next_document,
            self._menu_label("&Next Document", "window.next_document"),
        )
        window_menu.Append(
            self._id_previous_document,
            self._menu_label("&Previous Document", "window.previous_document"),
        )
        window_menu.AppendSeparator()
        window_menu.Append(
            self._id_send_to_tray,
            self._menu_label("Send to S&ystem Tray", "view.send_to_tray"),
        )

        self._id_word_count = wx.NewIdRef()
        self._id_sticky_notes = wx.NewIdRef()
        self._id_new_sticky_note = wx.NewIdRef()
        self._id_spell_check = wx.NewIdRef()
        self._id_previous_misspelling = wx.NewIdRef()
        self._id_next_misspelling = wx.NewIdRef()
        self._id_misspelling_list = wx.NewIdRef()
        self._id_dictionary_status = wx.NewIdRef()
        self._id_ocr_image = wx.NewIdRef()
        self._id_ocr_clipboard = wx.NewIdRef()
        self._id_ocr_screen = wx.NewIdRef()
        self._id_describe_image = wx.NewIdRef()
        self._id_regex_helper = wx.NewIdRef()
        self._id_pandoc_wizard = wx.NewIdRef()
        self._id_external_tools = wx.NewIdRef()
        self._id_read_aloud = wx.NewIdRef()
        self._id_read_aloud_stop = wx.NewIdRef()
        self._id_read_aloud_voice = wx.NewIdRef()
        self._id_read_aloud_settings = wx.NewIdRef()
        self._id_read_aloud_generate_audio = wx.NewIdRef()
        self._id_announcement_backend = wx.NewIdRef()
        self._id_announcement_backend_auto = wx.NewIdRef()
        self._id_announcement_backend_prism = wx.NewIdRef()
        self._id_announcement_backend_status_only = wx.NewIdRef()
        self._id_toggle_announcement_trace = wx.NewIdRef()
        self._id_dictation = wx.NewIdRef()
        self._id_dictation_voice_commands = wx.NewIdRef()
        self._id_bw_model_manager = wx.NewIdRef()
        self._id_bw_model_status = wx.NewIdRef()
        self._id_bw_model_recommend = wx.NewIdRef()
        self._id_bw_toggle_parakeet = wx.NewIdRef()
        self._id_bw_check_faster_whisper = wx.NewIdRef()
        self._id_bw_provider_center = wx.NewIdRef()
        self._id_bw_provider_status = wx.NewIdRef()
        self._id_bw_provider_recommend = wx.NewIdRef()
        self._id_bw_provider_select = wx.NewIdRef()
        self._id_bw_readiness_check = wx.NewIdRef()
        self._id_bw_capability_matrix = wx.NewIdRef()
        self._id_bw_download_queue = wx.NewIdRef()
        self._id_watch_folder_toggle = wx.NewIdRef()
        self._id_watch_folder_settings = wx.NewIdRef()
        self._id_watch_folder_status = wx.NewIdRef()
        self._id_document_intake_report = wx.NewIdRef()
        self._id_review_extraction_quality = wx.NewIdRef()
        self._id_report_bad_extraction = wx.NewIdRef()
        self._id_shell_install = wx.NewIdRef()
        self._id_shell_remove = wx.NewIdRef()
        self._id_notifications = wx.NewIdRef()
        self._id_check_updates = wx.NewIdRef()
        self._id_check_glow_updates = wx.NewIdRef()
        self._id_validate_contrast = wx.NewIdRef()
        self._id_status_bar_settings = wx.NewIdRef()
        self._id_share_export = wx.NewIdRef()
        self._id_share_import = wx.NewIdRef()
        self._id_keymap_editor = wx.NewIdRef()
        self._id_export_keymap = wx.NewIdRef()
        self._id_import_keymap = wx.NewIdRef()
        self._id_reset_keymap = wx.NewIdRef()
        self._id_profiles_and_features = wx.NewIdRef()
        self._id_glow_audit_document = wx.NewIdRef()
        self._id_glow_audit_selection = wx.NewIdRef()
        self._id_glow_fix_document = wx.NewIdRef()
        self._id_glow_fix_selection = wx.NewIdRef()
        self._id_link_inventory = wx.NewIdRef()
        self._id_ai_hub = wx.NewIdRef()
        self._id_ai_assistant = wx.NewIdRef()
        self._id_ai_prompt_studio = wx.NewIdRef()
        self._id_ai_agent_center = wx.NewIdRef()
        self._id_ai_accessibility_agent = wx.NewIdRef()
        self._id_ask_quill_chat = wx.NewIdRef()
        self._id_ai_enabled = wx.NewIdRef()
        self._id_ai_status_badge = wx.NewIdRef()
        self._id_ai_status_detail = wx.NewIdRef()
        self._id_ai_model = wx.NewIdRef()
        self._id_ai_session_browser = wx.NewIdRef()
        self._id_ai_connection = wx.NewIdRef()
        self._id_ai_forget_key = wx.NewIdRef()
        self._id_ai_rewrite_selection = wx.NewIdRef()
        self._id_ai_summarize_selection = wx.NewIdRef()
        self._id_ai_continue_writing = wx.NewIdRef()
        self._id_ai_fix_grammar = wx.NewIdRef()
        self._id_ai_speech_start_pause = wx.NewIdRef()
        self._id_ai_speech_stop = wx.NewIdRef()
        self._id_ai_speech_voice = wx.NewIdRef()
        self._id_ai_speech_settings = wx.NewIdRef()
        self._id_ai_speech_generate_audio = wx.NewIdRef()
        self._id_train_style = wx.NewIdRef()
        self._id_writing_instructions = wx.NewIdRef()
        self._id_compare_with_file = wx.NewIdRef()
        self._id_compare_open_documents = wx.NewIdRef()
        self._id_compare_next_difference = wx.NewIdRef()
        self._id_compare_previous_difference = wx.NewIdRef()
        self._id_compare_announce_difference = wx.NewIdRef()
        self._id_compare_difference_list = wx.NewIdRef()
        self._id_compare_toggle_sync = wx.NewIdRef()
        self._id_compare_options = wx.NewIdRef()
        self._id_compare_create_summary = wx.NewIdRef()
        self._id_compare_copy_current = wx.NewIdRef()
        self._id_compare_copy_all = wx.NewIdRef()
        self._id_start_macro_recording = wx.NewIdRef()
        self._id_stop_macro_recording = wx.NewIdRef()
        self._id_play_last_macro = wx.NewIdRef()
        self._id_manage_macros = wx.NewIdRef()
        self._id_open_welcome_guide = wx.NewIdRef()
        self._id_open_keyboard_reference = wx.NewIdRef()
        self._id_about_quill = wx.NewIdRef()
        self._id_save_diagnostics = wx.NewIdRef()
        self._id_report_bug = wx.NewIdRef()
        self._id_open_logs_folder = wx.NewIdRef()
        self._id_open_diagnostics_folder = wx.NewIdRef()
        self._id_context_help = wx.NewIdRef()
        self._id_help_status_page = wx.NewIdRef()
        self._id_why_dont_i_see_feature = wx.NewIdRef()
        self._id_switch_feature_profile = wx.NewIdRef()
        self._id_feature_profile_health_check = wx.NewIdRef()
        self._id_individual_feature_toggles = wx.NewIdRef()
        self._id_undo_profile_change = wx.NewIdRef()
        self._id_reset_feature_profile = wx.NewIdRef()
        self._id_profile_onboarding = wx.NewIdRef()
        self._id_keyboard_trap_snapshot = wx.NewIdRef()
        self._id_accessibility_audit = wx.NewIdRef()
        self._id_yaml_structure_editor = wx.NewIdRef()
        self._id_whisperer_about = wx.NewIdRef()
        tools_menu = wx.Menu()
        tools_menu.Append(
            self._id_palette,
            self._menu_label("&Command Palette...", "app.command_palette"),
        )
        tools_menu.AppendSeparator()
        sticky_notes_menu = wx.Menu()
        sticky_notes_menu.Append(
            self._id_sticky_notes,
            self._menu_label("&Sticky Notes...", "tools.sticky_notes"),
        )
        sticky_notes_menu.Append(
            self._id_new_sticky_note,
            self._menu_label("&New Sticky Note...", "tools.sticky_note_capture"),
        )
        tools_menu.AppendSubMenu(sticky_notes_menu, "&Sticky Notes")
        tools_menu.AppendSeparator()

        writing_menu = wx.Menu()
        writing_menu.Append(
            self._id_word_count,
            self._menu_label("&Word Count...", "tools.word_count"),
        )
        writing_menu.Append(
            self._id_spell_check,
            self._menu_label("&Spell Check...", "tools.spell_check_dialog"),
        )
        writing_menu.Append(
            self._id_previous_misspelling,
            self._menu_label("Previous Mi&sspelling", "tools.previous_misspelling"),
        )
        writing_menu.Append(
            self._id_next_misspelling,
            self._menu_label("Next &Misspelling", "tools.next_misspelling"),
        )
        writing_menu.Append(
            self._id_misspelling_list,
            self._menu_label("&Misspelling List...", "tools.misspelling_list"),
        )
        self._id_thesaurus = wx.NewIdRef()
        writing_menu.Append(
            self._id_thesaurus,
            self._menu_label("&Thesaurus...", "tools.thesaurus"),
        )
        writing_menu.Append(
            self._id_dictionary_status,
            self._menu_label("Dictionary &Status...", "tools.dictionary_status"),
        )
        tools_menu.AppendSubMenu(writing_menu, "&Writing and Language")

        read_aloud_menu = wx.Menu()
        read_aloud_menu.Append(
            self._id_read_aloud,
            self._menu_label("&Start / Pause", "tools.read_aloud_start_pause"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_stop,
            self._menu_label("S&top", "tools.read_aloud_stop"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_voice,
            self._menu_label("&Voice...", "tools.read_aloud_voice"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_settings,
            self._menu_label("Se&ttings...", "tools.read_aloud_settings"),
        )
        read_aloud_menu.Append(
            self._id_read_aloud_generate_audio,
            self._menu_label("Generate &Audio...", "tools.read_aloud_generate_audio"),
        )
        read_aloud_menu.Append(
            self._id_announcement_backend,
            self._menu_label("Announcement &Backend...", "tools.announcement_backend"),
        )
        backend_menu = wx.Menu()
        backend_menu.AppendRadioItem(
            self._id_announcement_backend_auto,
            "Automatic (Prism when available)",
        )
        backend_menu.AppendRadioItem(self._id_announcement_backend_prism, "Prism")
        backend_menu.AppendRadioItem(self._id_announcement_backend_status_only, "Status Bar Only")
        current_backend = self._announcement_engine.state().requested_backend
        backend_menu.Check(self._id_announcement_backend_auto, current_backend == "auto")
        backend_menu.Check(self._id_announcement_backend_prism, current_backend == "prism")
        backend_menu.Check(
            self._id_announcement_backend_status_only,
            current_backend == "status_only",
        )
        read_aloud_menu.AppendSubMenu(backend_menu, "Announcement Bac&kend")
        read_aloud_menu.Append(
            self._id_toggle_announcement_trace,
            "Announcement &Trace (in Settings)...",
        )
        tools_menu.AppendSubMenu(read_aloud_menu, "Read &Aloud")

        dictation_menu = wx.Menu()
        dictation_menu.Append(
            self._id_dictation,
            self._menu_label("&Dictation", "tools.dictation_toggle"),
            "Press to start dictation, press again to stop and insert",
        )
        dictation_menu.Append(
            self._id_dictation_voice_commands,
            "Hey QUILL &Commands (in Settings)...",
        )
        dictation_menu.AppendSeparator()
        dictation_menu.Append(
            self._id_watch_folder_toggle,
            "Watch Folder &Monitoring (in Settings)...",
        )
        dictation_menu.Append(
            self._id_watch_folder_settings,
            self._menu_label("Watch Folder &Profiles...", "tools.watch_folder_settings"),
        )
        dictation_menu.Append(
            self._id_watch_folder_status,
            self._menu_label("Watch Folder &Queue...", "tools.watch_folder_status"),
        )
        integrations_menu = wx.Menu()
        integrations_menu.Append(
            self._id_ocr_image,
            self._menu_label("OCR &Image...", "tools.ocr_image"),
        )
        integrations_menu.Append(
            self._id_ocr_clipboard,
            self._menu_label("OCR &Clipboard Image", "tools.ocr_clipboard"),
        )
        integrations_menu.Append(
            self._id_ocr_screen,
            self._menu_label("OCR &Screen Capture...", "tools.ocr_screen"),
        )
        integrations_menu.Append(
            self._id_describe_image,
            self._menu_label("&Describe Image...", "tools.describe_image"),
        )
        shell_menu = wx.Menu()
        shell_menu.Append(
            self._id_shell_install,
            self._menu_label("&Install Shell Integration...", "tools.shell_install"),
        )
        shell_menu.Append(
            self._id_shell_remove,
            self._menu_label("&Remove Shell Integration", "tools.shell_remove"),
        )
        integrations_menu.AppendSubMenu(shell_menu, "Sh&ell Integration")
        tools_menu.AppendSubMenu(integrations_menu, "&Integrations")

        intake_menu = wx.Menu()
        intake_menu.Append(
            self._id_document_intake_report,
            self._menu_label("&Document Intake Report...", "tools.document_intake_report"),
        )
        intake_menu.Append(
            self._id_review_extraction_quality,
            self._menu_label("&Review Extraction Quality...", "tools.review_extraction_quality"),
        )
        intake_menu.Append(
            self._id_report_bad_extraction,
            self._menu_label("R&eport Bad Extraction...", "tools.report_bad_extraction"),
        )
        tools_menu.AppendSubMenu(intake_menu, "Document &Intake")

        authoring_menu = wx.Menu()
        authoring_menu.Append(
            self._id_regex_helper,
            self._menu_label("Regex &Helper...", "tools.regex_helper"),
        )
        authoring_menu.Append(
            self._id_pandoc_wizard,
            self._menu_label("Pandoc Conversion &Wizard...", "tools.pandoc_wizard"),
        )
        authoring_menu.Append(
            self._id_external_tools,
            self._menu_label(
                "External Tools and Format &Support...",
                "tools.external_tools",
            ),
        )
        authoring_menu.Append(
            self._id_yaml_structure_editor,
            self._menu_label("&YAML Structure Editor...", "tools.yaml_structure_editor"),
        )
        ai_menu = wx.Menu()
        from quill.core.ai.model_manager import load_ai_enabled

        ai_menu.AppendCheckItem(self._id_ai_enabled, "Use Artificial &Intelligence")
        ai_menu.Check(self._id_ai_enabled, load_ai_enabled())
        ai_menu.AppendSeparator()
        ai_menu.Append(self._id_ai_status_badge, "AI Status: Not checked")
        ai_menu.Append(
            self._id_ai_status_detail, "AI Detail: Open AI Connection to verify settings"
        )
        ai_menu.Append(
            self._id_ai_hub,
            self._menu_label("AI &Hub...", "tools.ai_hub"),
        )
        ai_menu.Append(
            self._id_ask_quill_chat,
            self._menu_label("Ask Quill &Chat...", "tools.ask_quill_chat"),
        )
        ai_menu.Append(
            self._id_ai_model,
            self._menu_label("AI &Model and Connection...", "tools.ai_model"),
        )
        ai_menu.Append(
            self._id_ai_forget_key,
            "&Forget API Key",
        )
        ai_menu.Append(
            self._id_ai_session_browser,
            self._menu_label("Session &Branches...", "tools.ai_session_browser"),
        )
        ai_menu.Append(
            self._id_ai_assistant,
            self._menu_label("&Writing Assistant...", "tools.ai_assistant"),
        )
        ai_menu.Append(
            self._id_ai_prompt_studio,
            self._menu_label("Prompt &Studio...", "tools.ai_prompt_studio"),
        )
        ai_menu.Append(
            self._id_ai_agent_center,
            self._menu_label("Agent &Center...", "tools.ai_agent_center"),
        )
        ai_menu.Append(
            self._id_ai_accessibility_agent,
            self._menu_label("Accessibility &Tune-Up...", "tools.ai_accessibility_agent"),
        )
        ai_menu.Append(
            self._id_ai_rewrite_selection,
            self._menu_label("&Rewrite Selection", "tools.ai_rewrite_selection"),
        )
        ai_menu.Append(
            self._id_ai_summarize_selection,
            self._menu_label("&Summarize Selection", "tools.ai_summarize_selection"),
        )
        ai_menu.Append(
            self._id_ai_continue_writing,
            self._menu_label("&Continue Writing", "tools.ai_continue_writing"),
        )
        ai_menu.Append(
            self._id_ai_fix_grammar,
            self._menu_label("Fix &Grammar", "tools.ai_fix_grammar"),
        )
        ai_menu.Append(
            self._id_train_style,
            self._menu_label("&Train Writing Style...", "tools.train_writing_style"),
        )
        ai_menu.Append(
            self._id_writing_instructions,
            self._menu_label("&Writing Instructions...", "tools.writing_instructions"),
        )
        speech_menu = wx.Menu()
        speech_menu.Append(
            self._id_ai_speech_start_pause,
            self._menu_label("Start / &Pause", "tools.read_aloud_start_pause"),
        )
        speech_menu.Append(
            self._id_ai_speech_stop,
            self._menu_label("S&top", "tools.read_aloud_stop"),
        )
        speech_menu.Append(
            self._id_ai_speech_voice,
            self._menu_label("&Voice...", "tools.read_aloud_voice"),
        )
        speech_menu.Append(
            self._id_ai_speech_settings,
            self._menu_label("Se&ttings...", "tools.read_aloud_settings"),
        )
        speech_menu.Append(
            self._id_ai_speech_generate_audio,
            self._menu_label("Generate &Audio...", "tools.read_aloud_generate_audio"),
        )
        ai_menu.AppendSubMenu(speech_menu, "&Speech")
        menu_bar.Append(ai_menu, "A&I")
        whisperer_menu = wx.Menu()
        whisperer_menu.Append(
            self._id_whisperer_about,
            self._menu_label("&About Whisperer...", "whisperer.about"),
        )
        whisperer_menu.Append(
            self._id_profile_onboarding,
            self._menu_label("&Startup Wizard...", "help.startup_wizard"),
        )
        bw_dictation_menu = wx.Menu()
        bw_dictation_menu.Append(
            self._id_dictation,
            self._menu_label("&Dictation", "tools.dictation_toggle"),
            "Press to start dictation, press again to stop and insert",
        )
        bw_dictation_menu.Append(
            self._id_dictation_voice_commands,
            "Hey QUILL &Commands (in Settings)...",
        )
        bw_dictation_menu.AppendSeparator()
        bw_dictation_menu.Append(
            self._id_watch_folder_toggle,
            "Watch Folder &Monitoring (in Settings)...",
        )
        bw_dictation_menu.Append(
            self._id_watch_folder_settings,
            self._menu_label("Watch Folder &Profiles...", "tools.watch_folder_settings"),
        )
        bw_dictation_menu.Append(
            self._id_watch_folder_status,
            self._menu_label("Watch Folder &Queue...", "tools.watch_folder_status"),
        )
        whisperer_menu.AppendSubMenu(bw_dictation_menu, "&Dictation and Watch Folder")

        bw_models_menu = wx.Menu()
        self._append_bw_safe_mode_badge(bw_models_menu)
        bw_models_menu.Append(
            self._id_bw_model_manager,
            self._menu_label("&Model Manager...", "whisperer.model_manager"),
        )
        bw_models_menu.Append(
            self._id_bw_model_status,
            self._menu_label("Model &Status", "whisperer.model_status"),
        )
        bw_models_menu.Append(
            self._id_bw_model_recommend,
            self._menu_label("Use &Recommended Model", "whisperer.model_recommend"),
        )
        bw_models_menu.AppendCheckItem(
            self._id_bw_toggle_parakeet,
            self._menu_label("Show &Parakeet Models", "whisperer.toggle_parakeet"),
        )
        bw_models_menu.Check(
            self._id_bw_toggle_parakeet,
            bool(getattr(self.settings, "bw_enable_parakeet_models", False)),
        )
        bw_models_menu.AppendSeparator()
        bw_models_menu.Append(
            self._id_bw_check_faster_whisper,
            self._menu_label("Check &faster-whisper Engine", "whisperer.check_faster_whisper"),
        )
        bw_models_menu.Append(
            self._id_bw_download_queue,
            self._menu_label("Download &Queue...", "whisperer.download_queue"),
        )
        whisperer_menu.AppendSubMenu(bw_models_menu, "Speech &Models")

        bw_providers_menu = wx.Menu()
        self._append_bw_safe_mode_badge(bw_providers_menu)
        bw_providers_menu.Append(
            self._id_bw_provider_center,
            self._menu_label("&Provider Center...", "whisperer.provider_center"),
        )
        bw_providers_menu.Append(
            self._id_bw_provider_status,
            self._menu_label("Provider &Status", "whisperer.provider_status"),
        )
        bw_providers_menu.Append(
            self._id_bw_provider_recommend,
            self._menu_label("Use Re&commended Provider", "whisperer.provider_recommend"),
        )
        bw_providers_menu.Append(
            self._id_bw_provider_select,
            self._menu_label("&Select Provider...", "whisperer.provider_select"),
        )
        whisperer_menu.AppendSubMenu(bw_providers_menu, "&Providers")

        bw_rollout_menu = wx.Menu()
        self._append_bw_safe_mode_badge(bw_rollout_menu)
        bw_rollout_menu.Append(
            self._id_bw_readiness_check,
            self._menu_label("&Readiness Check", "whisperer.readiness_check"),
        )
        bw_rollout_menu.Append(
            self._id_bw_capability_matrix,
            self._menu_label("&Capability Matrix", "whisperer.capability_matrix"),
        )
        whisperer_menu.AppendSubMenu(bw_rollout_menu, "&Rollout")
        # BITS Whisperer is deferred to QUILL 2.0; the master `core.bw_whisperer`
        # flag is locked off for 1.0, so the whole menu stays hidden until the
        # suite reaches feature parity. Its commands are also feature-gated out of
        # the palette via the bw_* feature dependencies on this master flag.
        if self._feature_enabled("core.bw_whisperer"):
            menu_bar.Append(whisperer_menu, "&BITS Whisperer")
        glow_menu = wx.Menu()
        glow_menu.Append(
            self._id_glow_audit_document,
            self._menu_label("GLOW Audit Current &Document", "tools.glow_audit_document"),
        )
        glow_menu.Append(
            self._id_glow_audit_selection,
            self._menu_label("GLOW Audit &Selection", "tools.glow_audit_selection"),
        )
        glow_menu.AppendSeparator()
        glow_menu.Append(
            self._id_glow_fix_document,
            self._menu_label("&GLOW Fix Current Document", "tools.glow_fix_document"),
        )
        glow_menu.Append(
            self._id_glow_fix_selection,
            self._menu_label("GLOW Fix S&election", "tools.glow_fix_selection"),
        )
        authoring_menu.AppendSubMenu(glow_menu, "&GLOW")
        macro_menu = wx.Menu()
        macro_menu.Append(
            self._id_start_macro_recording,
            self._menu_label("&Start Recording", "tools.start_macro_recording"),
        )
        macro_menu.Append(
            self._id_stop_macro_recording,
            self._menu_label("S&top Recording", "tools.stop_macro_recording"),
        )
        macro_menu.Append(
            self._id_play_last_macro,
            self._menu_label("&Play Last Macro", "tools.play_last_macro"),
        )
        macro_menu.Append(
            self._id_manage_macros,
            self._menu_label("&Manage Macros...", "tools.manage_macros"),
        )
        authoring_menu.AppendSubMenu(macro_menu, "&Macros")
        convert_menu = wx.Menu()
        convert_menu.Append(
            self._id_sort_lines_ascending,
            self._menu_label("&Sort Lines Ascending", "edit.sort_lines_ascending"),
        )
        convert_menu.Append(
            self._id_sort_lines_descending,
            self._menu_label("Sort Lines &Descending", "edit.sort_lines_descending"),
        )
        convert_menu.Append(
            self._id_reverse_lines,
            self._menu_label("&Reverse Lines", "edit.reverse_lines"),
        )
        convert_menu.Append(
            self._id_remove_duplicate_lines,
            self._menu_label("Remove &Duplicate Lines", "edit.remove_duplicate_lines"),
        )
        convert_menu.AppendSeparator()
        convert_menu.Append(
            self._id_trim_trailing_whitespace,
            self._menu_label(
                "Trim Trailing &Whitespace",
                "edit.trim_trailing_whitespace",
            ),
        )
        convert_menu.Append(
            self._id_normalize_whitespace,
            self._menu_label("&Normalize Whitespace", "edit.normalize_whitespace"),
        )
        convert_menu.AppendSeparator()
        convert_menu.Append(
            self._id_convert_indentation_to_spaces,
            self._menu_label(
                "Convert Indentation to &Spaces",
                "edit.convert_indentation_to_spaces",
            ),
        )
        convert_menu.Append(
            self._id_convert_indentation_to_tabs,
            self._menu_label(
                "Convert Indentation to &Tabs",
                "edit.convert_indentation_to_tabs",
            ),
        )
        authoring_menu.AppendSubMenu(convert_menu, "Co&nvert")
        tools_menu.AppendSubMenu(authoring_menu, "Authoring && &Automation")

        compare_menu = wx.Menu()
        compare_menu.Append(self._id_compare_with_file, "Compare with &File...")
        compare_menu.Append(self._id_compare_open_documents, "Compare &Open Documents...")
        compare_menu.AppendSeparator()
        compare_menu.Append(self._id_compare_next_difference, "&Next Difference")
        compare_menu.Append(self._id_compare_previous_difference, "&Previous Difference")
        compare_menu.Append(self._id_compare_announce_difference, "&Announce Current Difference")
        compare_menu.Append(self._id_compare_difference_list, "Difference &List...")
        compare_menu.Append(self._id_compare_toggle_sync, "Toggle &Synchronized Navigation")
        compare_menu.Append(self._id_compare_options, "Compare O&ptions...")
        compare_menu.AppendSeparator()
        compare_menu.Append(self._id_compare_create_summary, "Create Difference &Summary")
        compare_menu.Append(self._id_compare_copy_current, "Copy &Current Difference")
        compare_menu.Append(self._id_compare_copy_all, "Copy A&ll Differences")
        tools_menu.AppendSubMenu(compare_menu, "&Compare Documents")

        accessibility_menu = wx.Menu()
        accessibility_menu.Append(self._id_accessibility_audit, "Accessibility A&udit...")
        accessibility_menu.Append(
            self._id_keyboard_trap_snapshot,
            "&Keyboard Trap && Tab-Order Snapshot...",
        )
        accessibility_menu.Append(self._id_validate_contrast, "&Validate Contrast...")
        accessibility_menu.Append(self._id_link_inventory, "Link Inventory && Alt-Text Catalo&g...")
        tools_menu.AppendSubMenu(accessibility_menu, "A&ccessibility")

        support_menu = wx.Menu()
        support_menu.Append(self._id_notifications, "Show &Notifications")
        support_menu.Append(self._id_report_bug, "&Report a Bug...")
        support_menu.Append(self._id_save_diagnostics, "Save &Diagnostics...")
        support_menu.Append(self._id_open_logs_folder, "Open &Logs Folder")
        support_menu.Append(
            self._id_open_diagnostics_folder,
            "Open &Diagnostics Folder",
        )
        support_menu.Append(self._id_check_updates, "Check for &Updates")
        tools_menu.AppendSubMenu(support_menu, "&Support")

        customize_menu = wx.Menu()
        customize_menu.Append(
            self._id_preferences,
            self._menu_label("Pre&ferences...", "app.preferences"),
        )
        customize_menu.Append(
            self._id_menu_editor,
            self._menu_label("Customize &Menus...", "app.menu_editor"),
        )
        customize_menu.AppendSeparator()
        customize_menu.Append(
            self._id_profiles_and_features,
            self._menu_label("&Profiles and Features...", "tools.profiles_and_features_settings"),
        )
        customize_menu.Append(self._id_status_bar_settings, "&Status Bar Layout...")
        customize_menu.AppendSeparator()
        customize_menu.Append(self._id_share_export, "&Export and Back Up...")
        customize_menu.Append(self._id_share_import, "&Import or Restore...")
        customize_menu.AppendSeparator()
        customize_menu.Append(self._id_keymap_editor, "&Keymap Editor...")
        customize_menu.Append(self._id_export_keymap, "&Export Keymap...")
        customize_menu.Append(self._id_import_keymap, "&Import Keymap...")
        customize_menu.Append(self._id_reset_keymap, "&Reset Keymap")
        tools_menu.AppendSubMenu(customize_menu, "&Customize")
        tools_menu.AppendSeparator()
        tools_menu.AppendSubMenu(self._build_edsharp_menu(), "Ed&Sharp Tools")
        tools_menu.AppendSubMenu(self._build_quillins_menu(), "&Quillins")
        menu_bar.Append(navigate_menu, "&Navigate")
        menu_bar.Append(format_menu, "F&ormat")
        menu_bar.Append(tools_menu, "&Tools")

        # The former top-level "Settings" menu is gone. All configuration now
        # lives together under Tools > Customize (Preferences, Customize Menus,
        # profiles/features, export/import, and keymap), which is the
        # Windows/Tools convention. Nothing references settings_menu after
        # this point; do not append it to the menu bar.

        help_menu = wx.Menu()
        help_menu.Append(
            self._id_context_help,
            self._menu_label("&What Can I Do Here?", "help.what_can_i_do_here"),
        )
        help_menu.Append(
            self._id_help_status_page,
            self._menu_label("Status &Page", "help.status_page"),
        )
        help_menu.Append(
            self._id_why_dont_i_see_feature,
            self._menu_label("&Why Don't I See a Feature?", "help.why_dont_i_see_feature"),
        )
        help_menu.AppendSeparator()
        self._id_open_user_guide = wx.NewIdRef()
        self._id_open_third_party_notices = wx.NewIdRef()
        help_menu.Append(self._id_open_user_guide, "Open User &Guide")
        help_menu.Append(
            self._id_open_third_party_notices,
            "Open &Third-Party Notices",
        )
        help_menu.Append(self._id_open_welcome_guide, "Open &Welcome Guide")
        help_menu.Append(self._id_open_keyboard_reference, "Open Keyboard &Reference")
        help_menu.Append(
            self._id_profile_onboarding,
            self._menu_label("&Startup Wizard...", "help.startup_wizard"),
        )
        help_menu.AppendSeparator()
        help_menu.Append(
            self._id_save_diagnostics,
            self._menu_label("Save &Diagnostics...", "help.save_diagnostics"),
        )
        help_menu.Append(
            self._id_report_bug,
            self._menu_label("Report a &Bug...", "help.report_bug"),
        )
        help_menu.AppendSeparator()
        profiles_menu = wx.Menu()
        profiles_menu.Append(
            self._id_switch_feature_profile,
            self._menu_label("&Switch Profile...", "help.switch_feature_profile"),
        )
        profiles_menu.Append(
            self._id_feature_profile_health_check,
            self._menu_label(
                "Profile &Health Check...",
                "help.feature_profile_health_check",
            ),
        )
        profiles_menu.Append(
            self._id_individual_feature_toggles,
            self._menu_label(
                "Manage &Individual Features...",
                "tools.individual_feature_toggles",
            ),
        )
        profiles_menu.AppendSeparator()
        profiles_menu.Append(
            self._id_undo_profile_change,
            self._menu_label("&Undo Last Profile Change", "help.undo_last_profile_change"),
        )
        profiles_menu.Append(
            self._id_reset_feature_profile,
            self._menu_label("Reset to &Essential Profile", "help.reset_feature_profile"),
        )
        help_menu.AppendSubMenu(profiles_menu, "Feature &Profiles")
        # "Check for Updates on Startup" lives in Settings now (removed the
        # duplicate Help-menu toggle).
        help_menu.Append(self._id_check_updates, "Check for &Updates...")
        help_menu.Append(self._id_check_glow_updates, "Check for &GLOW Updates...")
        help_menu.Append(self._id_about_quill, "&About Quill")
        menu_bar.Append(window_menu, "&Window")
        menu_bar.Append(help_menu, "&Help")

        self._apply_menu_customization(menu_bar)
        self.frame.SetMenuBar(menu_bar)
        self._refresh_contextual_menu_items()
        self._apply_ai_menu_enabled()

        self.frame.Bind(wx.EVT_MENU, lambda _e: self.new_file(), id=self._id_new)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_file(), id=self._id_open)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_url(), id=self._id_open_url)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_file(), id=self._id_save)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_file_as(), id=self._id_save_as)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.close_current_document(),
            id=self._id_close_document,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_all_files(), id=self._id_save_all)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reload_from_disk(),
            id=self._id_reload_from_disk,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.restore_backup(),
            id=self._id_restore_backup,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.save_session(), id=self._id_save_session)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_session(), id=self._id_open_session)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.page_setup(), id=self._id_page_setup)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.print_document(), id=self._id_print)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.save_as_plain_text(),
            id=self._id_save_plain_text,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_palette(), id=self._id_palette)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_preferences(), id=self._id_preferences)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.open_menu_editor(), id=self._id_menu_editor)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.exit_app(), id=self._id_exit)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_about_quill(), id=self._id_about_quill)
        # macOS routes the application-menu "About" to wx.ID_ABOUT — wire it to
        # the same custom dialog so the Apple-menu About shows the links too.
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_about_quill(), id=wx.ID_ABOUT)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_context_help(),
            id=self._id_context_help,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_help_status_page(),
            id=self._id_help_status_page,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_feature_explanation(),
            id=self._id_why_dont_i_see_feature,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.switch_feature_profile(),
            id=self._id_switch_feature_profile,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_feature_profile_health_check(),
            id=self._id_feature_profile_health_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_individual_feature_toggles(),
            id=self._id_individual_feature_toggles,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.undo_last_profile_change(),
            id=self._id_undo_profile_change,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reset_feature_profile_to_essential(),
            id=self._id_reset_feature_profile,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.run_startup_wizard(),
            id=self._id_profile_onboarding,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_whisperer_about_page(),
            id=self._id_whisperer_about,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_hub(),
            id=self._id_ai_hub,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_writing_assistant(),
            id=self._id_ai_assistant,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_prompt_studio(),
            id=self._id_ai_prompt_studio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_agent_center(),
            id=self._id_ai_agent_center,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.make_document_accessible(),
            id=self._id_ai_accessibility_agent,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ask_quill_chat(),
            id=self._id_ask_quill_chat,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self._refresh_ai_status(),
            id=self._id_ai_status_badge,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_preferences(),
            id=self._id_ai_status_detail,
        )
        self.frame.Bind(wx.EVT_MENU, self._on_toggle_ai_enabled, id=self._id_ai_enabled)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_model_settings(),
            id=self._id_ai_model,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self._forget_assistant_api_key(),
            id=self._id_ai_forget_key,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_session_browser(),
            id=self._id_ai_session_browser,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_preferences(),
            id=self._id_ai_connection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_rewrite_selection(),
            id=self._id_ai_rewrite_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_summarize_selection(),
            id=self._id_ai_summarize_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_continue_writing(),
            id=self._id_ai_continue_writing,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_ai_fix_grammar(),
            id=self._id_ai_fix_grammar,
        )
        self._refresh_ai_status()
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.send_to_tray(), id=self._id_send_to_tray)
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_tray_mode,
            id=self._id_toggle_tray_mode,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_soft_wrap,
            id=self._id_toggle_soft_wrap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_auto_side_preview,
            id=self._id_toggle_auto_side_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_tab_control,
            id=self._id_toggle_tab_control,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_find_wrap,
            id=self._id_toggle_find_wrap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_title_full_path,
            id=self._id_toggle_title_full_path,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_auto_check_updates,
            id=self._id_toggle_auto_check_updates,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("text"),
            id=self._id_dirty_title_text,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("asterisk"),
            id=self._id_dirty_title_asterisk,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_dirty_title_style("asterisk_text"),
            id=self._id_dirty_title_asterisk_text,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_dark_mode,
            id=self._id_toggle_dark_mode,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_persistent_undo,
            id=self._id_toggle_persistent_undo,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_spellcheck_as_you_type,
            id=self._id_toggle_spellcheck_as_you_type,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_intellisense_as_you_type,
            id=self._id_toggle_intellisense_as_you_type,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.preview_in_app(),
            id=self._id_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_side_preview(),
            id=self._id_split_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.focus_preview(),
            id=self._id_focus_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.preview_in_browser(),
            id=self._id_browser_preview,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_writing_assistant(),
            id=self._id_ai_assistant,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_train_writing_style(),
            id=self._id_train_style,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_writing_instructions(),
            id=self._id_writing_instructions,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_start_with_no_document_open,
            id=self._id_start_with_no_document_open,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.next_document(), id=self._id_next_document)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.previous_document(),
            id=self._id_previous_document,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.insert_link(), id=self._id_insert_link)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.follow_link(), id=self._id_follow_link)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.select_line(), id=self._id_select_line)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_paragraph(),
            id=self._id_select_paragraph,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.select_block(), id=self._id_select_block)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_start_of_line(),
            id=self._id_select_to_start_of_line,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_end_of_line(),
            id=self._id_select_to_end_of_line,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_start_of_document(),
            id=self._id_select_to_start_of_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_to_end_of_document(),
            id=self._id_select_to_end_of_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.sort_lines_ascending(),
            id=self._id_sort_lines_ascending,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.sort_lines_descending(),
            id=self._id_sort_lines_descending,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.reverse_lines(), id=self._id_reverse_lines)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.remove_duplicate_lines(),
            id=self._id_remove_duplicate_lines,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.trim_trailing_whitespace(),
            id=self._id_trim_trailing_whitespace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.normalize_whitespace(),
            id=self._id_normalize_whitespace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.convert_indentation_to_spaces(),
            id=self._id_convert_indentation_to_spaces,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.convert_indentation_to_tabs(),
            id=self._id_convert_indentation_to_tabs,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.set_mark(), id=self._id_set_mark)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.pop_mark(), id=self._id_pop_mark)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.exchange_point_and_mark(),
            id=self._id_exchange_point_mark,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.list_marks(), id=self._id_list_marks)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.undo(), id=self._id_undo)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.redo(), id=self._id_redo)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_with_source(),
            id=self._id_copy_with_source,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            self._on_toggle_extend_selection_mode,
            id=self._id_toggle_extend_selection_mode,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_text(), id=self._id_find)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.replace_text(), id=self._id_replace)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.replace_all_text(), id=self._id_replace_all)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_line(), id=self._id_go_to_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_page(), id=self._id_go_to_page)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_back_location(),
            id=self._id_back_location,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_forward_location(),
            id=self._id_forward_location,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_heading(),
            id=self._id_next_heading,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_heading(),
            id=self._id_previous_heading,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_block(),
            id=self._id_next_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_block(),
            id=self._id_previous_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_outline_navigator(),
            id=self._id_outline_navigator,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_heading_organizer(),
            id=self._id_heading_organizer,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.match_bracket(),
            id=self._id_match_bracket,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_structure(),
            id=self._id_next_structure,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_structure(),
            id=self._id_previous_structure,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_next_region(),
            id=self._id_next_region,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.navigate_previous_region(),
            id=self._id_previous_region,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.set_bookmark(), id=self._id_set_bookmark)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.go_to_bookmark(), id=self._id_go_to_bookmark)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.list_bookmarks(),
            id=self._id_list_bookmarks,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_next(), id=self._id_find_next)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.find_previous(), id=self._id_find_previous)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.find_all_matches(),
            id=self._id_find_all_matches,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.search_in_files(),
            id=self._id_search_in_files,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.replace_in_files(),
            id=self._id_replace_in_files,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_upper_case(), id=self._id_upper_case)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_lower_case(), id=self._id_lower_case)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_title_case(), id=self._id_title_case)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_sentence_case(),
            id=self._id_sentence_case,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_toggle_case(), id=self._id_toggle_case)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_toggle_line_comment(),
            id=self._id_toggle_line_comment,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_toggle_block_comment(),
            id=self._id_toggle_block_comment,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_indent(), id=self._id_indent)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_outdent(), id=self._id_outdent)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.move_line_up(), id=self._id_move_line_up)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.move_line_down(), id=self._id_move_line_down)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.duplicate_line(), id=self._id_duplicate_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.delete_line(), id=self._id_delete_line)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.join_lines(), id=self._id_join_lines)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_bold(), id=self._id_format_bold)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_italic(), id=self._id_format_italic)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(1), id=self._id_heading_1)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(2), id=self._id_heading_2)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(3), id=self._id_heading_3)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(4), id=self._id_heading_4)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(5), id=self._id_heading_5)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.format_heading(6), id=self._id_heading_6)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.decrease_heading_level(),
            id=self._id_decrease_heading_level,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.increase_heading_level(),
            id=self._id_increase_heading_level,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.style_headings(), id=self._id_style_headings)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_bullet_list(),
            id=self._id_insert_bullet_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_numbered_list(),
            id=self._id_insert_numbered_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_task_list(),
            id=self._id_insert_task_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_list_manager(),
            id=self._id_open_list_manager,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_code_block(),
            id=self._id_insert_code_block,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_footnote(),
            id=self._id_insert_footnote,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.format_insert_table(),
            id=self._id_insert_table,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.insert_html_tag(), id=self._id_insert_html_tag)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.insert_markdown_tag(),
            id=self._id_insert_markdown_tag,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.insert_snippet(),
            id=self._id_insert_snippet,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_snippets(),
            id=self._id_manage_snippets,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_word_prediction(),
            id=self._id_word_prediction,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_sticky_notes(),
            id=self._id_sticky_notes,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.create_sticky_note(),
            id=self._id_new_sticky_note,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_word_count(), id=self._id_word_count)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_spell_check_dialog(),
            id=self._id_spell_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.previous_misspelling(),
            id=self._id_previous_misspelling,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.next_misspelling(),
            id=self._id_next_misspelling,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_misspelling_list(),
            id=self._id_misspelling_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_thesaurus(),
            id=self._id_thesaurus,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_dictionary_status(),
            id=self._id_dictionary_status,
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.ocr_image_file(), id=self._id_ocr_image)
        self.frame.Bind(
            wx.EVT_MENU, lambda _e: self.ocr_clipboard_image(), id=self._id_ocr_clipboard
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.ocr_screen_capture(), id=self._id_ocr_screen)
        self.frame.Bind(
            wx.EVT_MENU, lambda _e: self.describe_image_with_ai(), id=self._id_describe_image
        )
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.show_regex_helper(), id=self._id_regex_helper)
        self.frame.Bind(wx.EVT_MENU, lambda _e: self.toggle_read_aloud(), id=self._id_read_aloud)
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_read_aloud(),
            id=self._id_read_aloud_stop,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_voice(),
            id=self._id_read_aloud_voice,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_settings(),
            id=self._id_read_aloud_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.generate_speech_audio(),
            id=self._id_read_aloud_generate_audio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_read_aloud(),
            id=self._id_ai_speech_start_pause,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_read_aloud(),
            id=self._id_ai_speech_stop,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_voice(),
            id=self._id_ai_speech_voice,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_read_aloud_settings(),
            id=self._id_ai_speech_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.generate_speech_audio(),
            id=self._id_ai_speech_generate_audio,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.choose_announcement_backend(),
            id=self._id_announcement_backend,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("auto"),
            id=self._id_announcement_backend_auto,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("prism"),
            id=self._id_announcement_backend_prism,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.set_announcement_backend("status_only"),
            id=self._id_announcement_backend_status_only,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_announcement_trace_capture(),
            id=self._id_toggle_announcement_trace,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_dictation(),
            id=self._id_dictation,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_dictation_voice_commands(),
            id=self._id_dictation_voice_commands,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_bw_model_manager(),
            id=self._id_bw_model_manager,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_bw_model_status(),
            id=self._id_bw_model_status,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.apply_bw_recommended_model(),
            id=self._id_bw_model_recommend,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_bw_parakeet_visibility(),
            id=self._id_bw_toggle_parakeet,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.check_bw_faster_whisper_engine(),
            id=self._id_bw_check_faster_whisper,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_bw_provider_center(),
            id=self._id_bw_provider_center,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_bw_provider_status(),
            id=self._id_bw_provider_status,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.apply_bw_recommended_provider(),
            id=self._id_bw_provider_recommend,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.select_bw_provider(),
            id=self._id_bw_provider_select,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_bw_readiness_check(),
            id=self._id_bw_readiness_check,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_bw_capability_matrix_page(),
            id=self._id_bw_capability_matrix,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_bw_download_queue(),
            id=self._id_bw_download_queue,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_watch_folder_monitoring(),
            id=self._id_watch_folder_toggle,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_watch_folder_settings(),
            id=self._id_watch_folder_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_watch_folder_status(),
            id=self._id_watch_folder_status,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_document_intake_report(),
            id=self._id_document_intake_report,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.review_extraction_quality(),
            id=self._id_review_extraction_quality,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.report_bad_extraction(),
            id=self._id_report_bad_extraction,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_pandoc_wizard(),
            id=self._id_pandoc_wizard,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_external_tools_dialog(),
            id=self._id_external_tools,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.install_shell_integration(),
            id=self._id_shell_install,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.remove_shell_integration(),
            id=self._id_shell_remove,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_notifications(),
            id=self._id_notifications,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.check_for_updates(),
            id=self._id_check_updates,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.check_for_glow_updates(),
            id=self._id_check_glow_updates,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.validate_contrast(),
            id=self._id_validate_contrast,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_status_bar_settings(),
            id=self._id_status_bar_settings,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_share_export_dialog(),
            id=self._id_share_export,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_share_import_dialog(),
            id=self._id_share_import,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_keymap_editor(),
            id=self._id_keymap_editor,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_profiles_and_features_settings(),
            id=self._id_profiles_and_features,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_link_inventory(),
            id=self._id_link_inventory,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_with_file(),
            id=self._id_compare_with_file,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_open_documents(),
            id=self._id_compare_open_documents,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_next_difference(),
            id=self._id_compare_next_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_previous_difference(),
            id=self._id_compare_previous_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.compare_announce_difference(),
            id=self._id_compare_announce_difference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_compare_difference_list(),
            id=self._id_compare_difference_list,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.toggle_compare_synchronization(),
            id=self._id_compare_toggle_sync,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_compare_options(),
            id=self._id_compare_options,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.create_compare_summary_document(),
            id=self._id_compare_create_summary,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_current_difference(),
            id=self._id_compare_copy_current,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.copy_all_differences(),
            id=self._id_compare_copy_all,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.start_macro_recording(),
            id=self._id_start_macro_recording,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.stop_macro_recording(),
            id=self._id_stop_macro_recording,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.play_last_macro(),
            id=self._id_play_last_macro,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.manage_macros(),
            id=self._id_manage_macros,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.export_keymap_file(),
            id=self._id_export_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.import_keymap_file(),
            id=self._id_import_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.reset_keymap_defaults(),
            id=self._id_reset_keymap,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_welcome_guide(),
            id=self._id_open_welcome_guide,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_keyboard_reference(),
            id=self._id_open_keyboard_reference,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_user_guide(),
            id=self._id_open_user_guide,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_third_party_notices(),
            id=self._id_open_third_party_notices,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.save_diagnostics_bundle(),
            id=self._id_save_diagnostics,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.report_bug(),
            id=self._id_report_bug,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_logs_folder(),
            id=self._id_open_logs_folder,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_diagnostics_folder(),
            id=self._id_open_diagnostics_folder,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.open_yaml_structure_editor(),
            id=self._id_yaml_structure_editor,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_accessibility_audit(),
            id=self._id_accessibility_audit,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_document(),
            id=self._id_glow_audit_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_audit_selection(),
            id=self._id_glow_audit_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_document(),
            id=self._id_glow_fix_document,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.glow_fix_selection(),
            id=self._id_glow_fix_selection,
        )
        self.frame.Bind(
            wx.EVT_MENU,
            lambda _e: self.show_keyboard_trap_snapshot(),
            id=self._id_keyboard_trap_snapshot,
        )
        self.frame.Bind(wx.EVT_MENU, self._on_open_recent)
        self.frame.Bind(wx.EVT_MENU, self._on_session_menu)
        self.frame.Bind(wx.EVT_MENU, self._on_recent_session_menu)
        self.frame.Bind(wx.EVT_MENU, self._on_menu_command_activity)
