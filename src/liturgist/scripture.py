"""
Scripture reference parsing and text extraction.

Parses references like "Jude 3", "John 3:16", or "Romans 8:28-30" and pulls
the corresponding verse text out of bible JSON data.
"""

import re
import sys
from typing import Any


def get_scripture_text(data: dict[str, Any], passage: str) -> str:
    """
    Extract scripture text from bible data for a given passage.

    Args:
        data: Dictionary containing bible data with books/chapters/verses
        passage: Scripture reference (e.g. "Jude 3", "John 3:16", or "Romans 8:28-30")

    Returns:
        Formatted scripture text with verse numbers
    """
    result = ""

    pattern = r"(?P<book>(?:[1-3]\s)?[A-Za-z]+(?:\s[A-Za-z]+)*)\s*\d*(?:\s*:\s*\d+(?:\s*-\s*\d+)?|(?:\s*-\s*\d+))?"
    match_iter = re.finditer(pattern, passage)
    current_match = next(match_iter, None)

    while current_match is not None:
        match_book = current_match.group("book")
        book = next(
            (book for book in data["books"] if book["name"] == match_book), None
        )
        if book is None:
            print(f"Cannot find book {match_book}", file=sys.stderr)
            break

        chapters = book["chapters"]
        verses = []

        verse_pattern = (
            # Single chapter book refs might omit chapter segment
            r"[1-3]?\s?[A-Za-z]+(?:\s[A-Za-z]+)*(?:\s*1:)?(?P<start>\s*\d+)?(?:\s*-\s*(?P<end>\d+))?"
            if len(chapters) == 1
            # Multi chapter book refs must specify the chapter
            else r"[1-3]?\s?[A-Za-z ]+ (?P<chapter>\d+)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?"
        )

        precise_match = next(re.finditer(verse_pattern, current_match.group()), None)
        precise_match_start = precise_match.group("start")
        precise_match_end = (
            int(precise_match.group("end"))
            if precise_match.group("end")
            else precise_match_start
        )

        chapter = (
            chapters[0]
            if len(chapters) == 1
            else chapters[int(precise_match.group("chapter")) - 1]
        )

        if precise_match_start is not None:
            start_verse_index = int(precise_match_start) - 1
            end_verse_index = int(precise_match_end)

            selected = chapter["verses"][start_verse_index:end_verse_index]
            if len(selected) == 1:
                verses = [selected[0]]
            else:
                verses = [
                    f"{idx + 1 + start_verse_index}. {verse}"
                    for idx, verse in enumerate(selected)
                ]
        else:
            verses = [
                f"{idx + 1}. {verse}" for idx, verse in enumerate(chapter["verses"])
            ]

        next_match = next(match_iter, None)

        if next_match is None:
            result = result + " ".join(verses)
        else:
            result = result + " ".join(verses) + " (...) "

        current_match = next_match

    return result
