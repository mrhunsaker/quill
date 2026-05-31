from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable

from quill.core.commands import Command

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")

_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}

_WAKE_PHRASES = ("hey quill", "quill")


@dataclass(frozen=True, slots=True)
class VoiceCommandMatch:
    command_id: str
    alias: str
    transcript: str


def normalize_voice_text(text: str) -> str:
    cleaned = text.lower().replace("&", " and ")
    cleaned = _NON_ALNUM.sub(" ", cleaned)
    tokens = [_NUMBER_WORDS.get(token, token) for token in cleaned.split()]
    return _WHITESPACE.sub(" ", " ".join(tokens)).strip()


def build_voice_command_aliases(
    commands: Iterable[Command],
    extra_aliases: dict[str, str] | None = None,
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for command in commands:
        candidates = (
            command.title,
            command.id.rsplit(".", 1)[-1].replace("_", " "),
            command.id.replace(".", " "),
        )
        for candidate in candidates:
            alias = normalize_voice_text(candidate)
            if alias and alias not in aliases:
                aliases[alias] = command.id
    if extra_aliases is not None:
        for alias, command_id in extra_aliases.items():
            normalized = normalize_voice_text(alias)
            if normalized:
                aliases[normalized] = command_id
    return aliases


def extract_transcript_body(transcript: str) -> str | None:
    normalized = normalize_voice_text(transcript)
    for wake_phrase in _WAKE_PHRASES:
        if normalized == wake_phrase:
            return ""
        prefix = f"{wake_phrase} "
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return None


def resolve_voice_command(
    transcript: str,
    aliases: dict[str, str],
) -> VoiceCommandMatch | None:
    body = extract_transcript_body(transcript)
    if body is None or not body:
        return None
    for alias in sorted(aliases, key=len, reverse=True):
        if body == alias:
            return VoiceCommandMatch(command_id=aliases[alias], alias=alias, transcript=body)
    return None


def split_text_delta(before: str, after: str) -> tuple[str, str, str]:
    prefix_length = 0
    prefix_limit = min(len(before), len(after))
    while prefix_length < prefix_limit and before[prefix_length] == after[prefix_length]:
        prefix_length += 1

    suffix_length = 0
    before_limit = len(before) - prefix_length
    after_limit = len(after) - prefix_length
    while (
        suffix_length < before_limit
        and suffix_length < after_limit
        and before[len(before) - suffix_length - 1] == after[len(after) - suffix_length - 1]
    ):
        suffix_length += 1

    prefix = after[:prefix_length]
    inserted = after[prefix_length : len(after) - suffix_length if suffix_length else len(after)]
    suffix = after[len(after) - suffix_length :] if suffix_length else ""
    return prefix, inserted, suffix
