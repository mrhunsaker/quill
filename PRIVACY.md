# Privacy Statement

This document describes how QUILL handles privacy for local and AI-assisted workflows.

## Core privacy commitments

1. QUILL is local-first by design.
2. QUILL does not persist AI chat session transcripts by default.
3. QUILL does not send network requests without explicit user action.
4. QUILL does not store document content in API-key storage or credential vault records.

## AI interaction data

When you use cloud AI providers, the prompt content you choose to send is transmitted to that provider. Provider-side storage, retention, and policy behavior are controlled by that provider's terms and settings, not QUILL.

QUILL does not persist Ask Quill chat transcripts or Writing Assistant interaction transcripts by default. If you explicitly copy output into a document, that content is then part of your document and saved according to your normal file and backup workflow.

## Key and credential handling

QUILL stores API keys using Windows Credential Manager when available. If Credential Manager is unavailable, QUILL falls back to DPAPI-encrypted local secret storage.

QUILL does not store API keys in plaintext.

## Local files QUILL may create

QUILL may create local settings and state files under your app data directory (for example `%APPDATA%\Quill\...`), including:

- editor and application settings
- onboarding state
- feature and UI preferences
- optional encrypted secret metadata

These files are local to your machine and are not uploaded by default.

## User responsibility

You are responsible for reviewing AI-generated output before using, sharing, or publishing it. For sensitive content, use local models when possible and verify that cloud use meets your organization's security and compliance requirements.
