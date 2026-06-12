/**
 * QUILL Developer Console TypeScript type definitions.
 *
 * The `quill` global is available in the TypeScript console.
 * Copy this file into your project to get completion and documentation.
 */

interface QuillDocumentSnapshot {
  name: string;
  lineCount: number;
}

interface QuillDocumentStats {
  words: number;
  lines: number;
  chars: number;
}

interface QuillConsoleApi {
  /** Insert text at the current caret position. */
  insertText(text: string): Promise<void>;

  /** Replace the current selection with text (or insert if no selection). */
  replaceSelection(text: string): Promise<void>;

  /** Return the currently selected text. */
  selectedText(): Promise<string>;

  /** Return the full document text. */
  documentText(): Promise<string>;

  /** Alias for documentText(). */
  getText(): Promise<string>;

  /** Replace the entire document with text. */
  setDocumentText(text: string): Promise<void>;

  /** Move the caret to a 1-based line number. */
  gotoLine(line: number): Promise<void>;

  /** Move the caret to a 0-based character offset. */
  gotoOffset(offset: number): Promise<void>;

  /** Run a registered QUILL command by ID. */
  runCommand(commandId: string, args?: Record<string, unknown>): Promise<void>;

  /** Return true if commandId is registered. */
  commandExists(commandId: string): Promise<boolean>;

  /** Send a screen-reader announcement. */
  announce(text: string): Promise<void>;

  /** Return a snapshot of the active document. */
  activeDocument(): Promise<QuillDocumentSnapshot>;

  /** Return word, line, and character counts for the active document. */
  documentStats(): Promise<QuillDocumentStats>;

  /** Return the last screen-reader announcement. */
  lastAnnouncement(): Promise<string>;
}

declare const quill: QuillConsoleApi;
