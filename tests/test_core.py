"""Tests for liturgist.core module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from liturgist.core import (
    load_template_from_file,
    next_sunday,
    process_schedule_data,
    read_schedule,
)


def test_next_sunday():
    """Test next_sunday function returns a date."""
    result = next_sunday()
    assert isinstance(result, type(datetime.now().date()))


def test_read_schedule_csv():
    """Test reading a CSV schedule file."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("Header Row\n")
        f.write("Date,Hymn 1,Scripture 1\n")
        f.write("2024-02-18,Hymn 290,Acts 2:34-35\n")
        temp_path = f.name

    try:
        df = read_schedule(temp_path)
        assert isinstance(df, pd.DataFrame)
        assert "Date" in df.columns
        assert "Hymn 1" in df.columns
        assert "Scripture 1" in df.columns
    finally:
        Path(temp_path).unlink()


def test_read_schedule_unsupported():
    """Test reading an unsupported file format raises ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Unexpected schedule file type"):
            read_schedule(temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_template_from_file():
    """Test loading a template file."""
    template_content = "Hello {{name}}!"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(template_content)
        temp_path = f.name

    try:
        template = load_template_from_file(temp_path)
        result = template({"name": "World"})
        assert result == "Hello World!"
    finally:
        Path(temp_path).unlink()


def test_process_schedule_data():
    """Test processing schedule data for a date."""
    # Create test schedule DataFrame
    data = {
        "Date": ["2024-02-18"],
        "Hymn 1": ["Hymn 290 - Hallelujah, Praise Jehovah"],
        "Scripture 1": ["Acts 2:34-35"],
        "Extra 1 - Question": ["Q50. What is required in the second commandment?"],
        "Extra 2 - Answer": [
            "A. The second commandment requireth the receiving, observing, and keeping pure and entire, all such religious worship and ordinances as God hath appointed in his Word."
        ],
    }
    schedule = pd.DataFrame(data)

    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["DATE"] == "2024-02-18"
    assert result["FORMATTED_DATE"] == "Sunday, February 18, 2024"
    assert result["HYMNS"] == ["Hymn 290 - Hallelujah, Praise Jehovah"]
    assert result["SCRIPTURE_REFS"] == ["Acts 2:34-35"]
    assert result["EXTRAS"] == [
        "Q50. What is required in the second commandment?",
        "A. The second commandment requireth the receiving, observing, and keeping pure and entire, all such religious worship and ordinances as God hath appointed in his Word.",
    ]


def test_scripture_array_from_numbered_columns():
    """Test that multiple Scripture N columns build a SCRIPTURE_REFS array."""
    data = {
        "Date": ["2024-02-18"],
        "Scripture 1": ["Genesis 1:1"],
        "Scripture 2": ["Psalm 23:1-3"],
        "Scripture 3": ["John 3:16"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["SCRIPTURE_REFS"] == ["Genesis 1:1", "Psalm 23:1-3", "John 3:16"]


def test_scripture_array_with_descriptive_headings():
    """Test that columns like 'Scripture 1 - Call to Worship' match Scripture 1."""
    data = {
        "Date": ["2024-02-18"],
        "Scripture 1 - Call to Worship": ["Genesis 1:1"],
        "Scripture 2 - Prayer Verse": ["Psalm 23:1-3"],
        "Scripture 3 - Assurance": ["John 3:16"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["SCRIPTURE_REFS"] == ["Genesis 1:1", "Psalm 23:1-3", "John 3:16"]


def test_scripture_heading_does_not_match_longer_number():
    """Test that 'Scripture 1' does not match a column named 'Scripture 10'."""
    data = {
        "Date": ["2024-02-18"],
        "Scripture 1": ["Genesis 1:1"],
        "Scripture 10": ["Psalm 23:1-3"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["SCRIPTURE_REFS"][0] == "Genesis 1:1"
    assert result["SCRIPTURE_REFS"][9] == "Psalm 23:1-3"
    assert all(v is None for v in result["SCRIPTURE_REFS"][1:9])


def test_scripture_text_expansion_as_array():
    """Test that EXPANDED_SCRIPTURE_REFS is built as an array matching SCRIPTURE_REFS."""
    data = {
        "Date": ["2024-02-18"],
        "Scripture 1": ["John 3:16"],
        "Scripture 2": ["Jude 3"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date, bible_json_path="samples/kjv.json")

    assert isinstance(result["EXPANDED_SCRIPTURE_REFS"], list)
    assert len(result["EXPANDED_SCRIPTURE_REFS"]) == 2
    assert "For God so loved the world" in result["EXPANDED_SCRIPTURE_REFS"][0]
    assert "earnestly contend for the faith" in result["EXPANDED_SCRIPTURE_REFS"][1]


def test_hymn_heading_prefix_match():
    """Test that descriptive hymn headings like 'Hymn 1 - Processional' also work."""
    data = {
        "Date": ["2024-02-18"],
        "Hymn 1 - Processional": ["Hymn 290 - Hallelujah"],
        "Hymn 2 - Confession": ["Hymn 620 - Stricken"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["HYMNS"] == ["Hymn 290 - Hallelujah", "Hymn 620 - Stricken"]


def test_extras_array_with_descriptive_headings():
    """Test that 'Extra N - <label>' columns build the EXTRAS array."""
    data = {
        "Date": ["2024-02-18"],
        "Extra 1 - Collect": ["O God, who..."],
        "Extra 2 - Question": ["Q50. What is required..."],
        "Extra 3 - Answer": ["A. The second commandment..."],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["EXTRAS"] == [
        "O God, who...",
        "Q50. What is required...",
        "A. The second commandment...",
    ]


def test_array_preserves_gaps_as_none():
    """Test that missing columns in the middle produce None, not a shifted array."""
    data = {
        "Date": ["2024-02-18"],
        "Scripture 1": ["Genesis 1:1"],
        "Scripture 3": ["John 3:16"],
    }
    schedule = pd.DataFrame(data)
    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["SCRIPTURE_REFS"] == ["Genesis 1:1", None, "John 3:16"]


def test_process_schedule_data_date_not_found():
    """Test processing schedule data with date not in schedule."""
    data = {
        "Date": [pd.to_datetime("2024-02-18").date()],
        "Hymn 1": ["Hymn 290"],
    }
    schedule = pd.DataFrame(data)

    date = pd.to_datetime("2024-02-25").date()

    with pytest.raises(ValueError, match="Date .* was not found in the schedule"):
        process_schedule_data(schedule, date)
