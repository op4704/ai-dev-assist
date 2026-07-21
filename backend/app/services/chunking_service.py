"""
Splits file content into overlapping, token-budgeted chunks for embedding.
Uses a lightweight char-based token approximation (no tiktoken — avoids
the network dependency on first use).
"""
from dataclasses import dataclass

CHARS_PER_TOKEN = 4


@dataclass
class ChunkResult:
    content: str
    start_line: int
    end_line: int
    token_count: int
    chunk_index: int


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def _flatten_lines(lines: list[str], max_chars: int) -> list[tuple[str, int]]:
    """
    Returns (piece, original_line_number) pairs. Any single line longer than
    max_chars gets hard-split into multiple pieces so no single piece can
    ever blow the token budget on its own.
    """
    flattened: list[tuple[str, int]] = []
    for i, line in enumerate(lines, start=1):
        if len(line) <= max_chars:
            flattened.append((line, i))
        else:
            for start in range(0, len(line), max_chars):
                flattened.append((line[start:start + max_chars], i))
    return flattened


def chunk_text(
    content: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 50,
) -> list[ChunkResult]:
    if not content or not content.strip():
        return []

    raw_lines = content.splitlines()
    if not raw_lines:
        return []

    chunk_size_chars = chunk_size_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    # Cap any single piece at chunk_size_chars so oversized lines can't escape the budget
    pieces = _flatten_lines(raw_lines, chunk_size_chars)
    piece_lengths = [len(p) + 1 for p, _ in pieces]

    chunks: list[ChunkResult] = []
    n = len(pieces)
    start_idx = 0
    chunk_index = 0

    while start_idx < n:
        char_count = 0
        end_idx = start_idx

        while end_idx < n and char_count < chunk_size_chars:
            char_count += piece_lengths[end_idx]
            end_idx += 1

        chunk_pieces = pieces[start_idx:end_idx]
        chunk_content = "\n".join(p for p, _ in chunk_pieces)

        chunks.append(
            ChunkResult(
                content=chunk_content,
                start_line=chunk_pieces[0][1],
                end_line=chunk_pieces[-1][1],
                token_count=_estimate_tokens(chunk_content),
                chunk_index=chunk_index,
            )
        )
        chunk_index += 1

        if end_idx >= n:
            break

        back_chars = 0
        back_idx = end_idx
        while back_idx > start_idx and back_chars < overlap_chars:
            back_idx -= 1
            back_chars += piece_lengths[back_idx]

        start_idx = back_idx if back_idx > start_idx else end_idx

    return chunks