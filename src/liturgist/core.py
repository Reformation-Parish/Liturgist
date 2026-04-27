"""
Core functionality for liturgical document generation.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from pybars import Compiler

from .hymnal import load_hymnal_scores

hymn_csv_keys = [f"Hymn {i}" for i in range(1, 50)]
scripture_csv_keys = [f"Scripture {i}" for i in range(1, 50)]

csv_key_to_template_key = {
    **dict.fromkeys(hymn_csv_keys, "HYMNS"),
    **dict.fromkeys(scripture_csv_keys, "SCRIPTURE_REFS"),
    "Question": "CATECHISM_QUESTION",
    "Answer": "CATECHISM_ANSWER",
    "Baptisms": "BAPTISMS",
    "Collect": "COLLECT",
    "Church of the Month": "CHURCH_OF_THE_MONTH",
}


def next_sunday() -> datetime:
    """Calculate the date of the next Sunday."""
    current_datetime = datetime.now()
    current_weekday = current_datetime.weekday()

    if current_weekday == 6 and current_datetime.hour < 12:
        next_sunday = current_datetime
    elif current_weekday == 6:
        next_sunday = current_datetime + timedelta(days=7)
    else:
        next_sunday = current_datetime + timedelta(days=6 - current_weekday)

    return next_sunday.date()


def read_schedule(schedule_path: str | Path) -> pd.DataFrame:
    """
    Read a schedule file (CSV, ODS, XLSX, or XLS) and return as DataFrame.

    Args:
        schedule_path: Path to the schedule file

    Returns:
        pandas DataFrame containing the schedule data

    Raises:
        ValueError: If file extension is not supported
    """
    schedule_path = Path(schedule_path)
    file_extension = schedule_path.suffix.lower()

    if file_extension == ".csv":
        return pd.read_csv(schedule_path, header=1)
    elif file_extension == ".ods":
        return pd.read_excel(schedule_path, header=1, engine="odf")
    elif file_extension in [".xlsx", ".xls"]:
        return pd.read_excel(schedule_path, header=1)
    else:
        raise ValueError(f"Unexpected schedule file type: {file_extension}")


def load_template_from_file(template_path: str | Path) -> Any:
    """
    Load and compile a Handlebars template from file.

    Args:
        template_path: Path to the template file

    Returns:
        A function which applies its data arguments to the template.
    """
    template_path = Path(template_path)
    template_source = template_path.read_text(encoding="utf-8")
    compiler = Compiler()
    return compiler.compile(template_source)


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


def _find_column(csv_key: str, columns: pd.Index) -> str | None:
    """Find a column that matches the csv_key exactly or starts with it.

    A column matches if it equals the key, or starts with the key followed by
    a non-digit character (so "Scripture 1" won't match "Scripture 10").
    """
    for col in columns:
        if col == csv_key:
            return col
        if col.startswith(csv_key) and not col[len(csv_key)].isdigit():
            return col
    return None


def process_schedule_data(
    schedule: pd.DataFrame,
    date: date,
    bible_json_path: str | Path | None = None,
    hymnal_dir: str | Path | None = None,
) -> dict[str, Any]:
    """
    Process schedule data for a specific date and return template data.

    Args:
        schedule: DataFrame containing schedule data
        date: Date to extract data for
        bible_json_path: Optional path to bible JSON file for scripture text
        hymnal_dir: Optional path to directory containing hymn sheet music files

    Returns:
        Dictionary of processed data for template rendering

    Raises:
        ValueError: If date is not found in schedule
    """

    # Handle different date column types for comparison
    if pd.api.types.is_datetime64_any_dtype(schedule["Date"]):
        # For datetime columns (from Excel files), extract date part
        week = schedule[schedule["Date"].dt.date == date]
    else:
        # For string or date columns, convert to datetime first, then extract date
        schedule_dates = pd.to_datetime(schedule["Date"])
        week = schedule[schedule_dates.dt.date == date]

    if week.empty:
        raise ValueError(f"Date {date} was not found in the schedule.")

    iso_date = date.strftime("%Y-%m-%d")
    formatted_date = date.strftime("%A, %B %d, %Y")

    data = {
        "DATE": iso_date,
        "FORMATTED_DATE": formatted_date,
    }

    # Process CSV keys to template keys
    for csv_key, template_key in csv_key_to_template_key.items():
        column = _find_column(csv_key, week.columns)

        # For numbered array keys, use positional insertion so gaps
        # are preserved as None rather than shifting indices.
        parts = csv_key.rsplit(" ", 1)
        is_array_key = len(parts) == 2 and parts[1].isdigit()

        if is_array_key:
            idx = int(parts[1]) - 1
            if template_key not in data:
                data[template_key] = []
            arr = data[template_key]
            while len(arr) <= idx:
                arr.append(None)
            if column is not None:
                value = week[column].iloc[0]
                if not pd.isnull(value):
                    arr[idx] = value
        else:
            if column is not None:
                value = week[column].iloc[0]
                if not pd.isnull(value):
                    data[template_key] = value

    # Trim trailing None entries from array values
    for value in data.values():
        if isinstance(value, list):
            while value and value[-1] is None:
                value.pop()

    # Process bible JSON if provided
    if bible_json_path is not None:
        json_path = Path(bible_json_path)
        if json_path.is_file():
            bible_text = json_path.read_text(encoding="utf-8")
            bible_data = json.loads(bible_text)
            scriptures = data.get("SCRIPTURE_REFS")
            if scriptures is not None:
                if not isinstance(scriptures, list):
                    scriptures = [scriptures]
                data["EXPANDED_SCRIPTURE_REFS"] = [
                    get_scripture_text(bible_data, ref) if ref is not None else None
                    for ref in scriptures
                ]

    # Load hymnal scores if provided
    if hymnal_dir is not None:
        hymnal_path = Path(hymnal_dir)
        if hymnal_path.is_dir():
            hymns = data.get("HYMNS", [])
            data["HYMN_SCORES"] = load_hymnal_scores(hymns, hymnal_path)

    return data
