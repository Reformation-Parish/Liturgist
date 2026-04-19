"""Tests for liturgist.core module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from liturgist.core import (
    get_scripture_text,
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
        f.write("Date,Hymn 1,Scripture 0\n")
        f.write("2024-02-18,Hymn 290,Acts 2:34-35\n")
        temp_path = f.name

    try:
        df = read_schedule(temp_path)
        assert isinstance(df, pd.DataFrame)
        assert "Date" in df.columns
        assert "Hymn 1" in df.columns
        assert "Scripture 0" in df.columns
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


def test_get_scripture_text():
    """Test scripture text extraction."""
    bible_data = {"books": []}

    result = get_scripture_text(bible_data, "John 3:16")
    assert result == ""


def test_chapter_verse_range_reference_found():
    """Test reference of the form BOOK CHAPTER:START-END."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "John 3:16-17")
    assert (
        result
        == "16. ‹For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.› 17. ‹For God sent not his Son into the world to condemn the world; but that the world through him might be saved.›"
    )


def test_non_contiguous_references_found():
    """Test multiple references are matched."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "John 3:16-17 John 4:1")
    assert (
        result
        == "16. ‹For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.› 17. ‹For God sent not his Son into the world to condemn the world; but that the world through him might be saved.› (...) 1. When therefore the Lord knew how the Pharisees had heard that Jesus made and baptized more disciples than John,"
    )


def test_chapter_verse_reference_found():
    """Test full reference of the form BOOK CHAPTER:START."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "John 3:16")
    assert (
        result
        == "16. ‹For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.›"
    )


def test_chapter_reference_found():
    """Test reference of the form BOOK CHAPTER."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "John 3")
    assert len(result) > 0


def test_chapterless_reference_found():
    """Test reference of the form BOOK VERSE."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "Jude 3")
    assert (
        result
        == "3. Beloved, when I gave all diligence to write unto you of the common salvation, it was needful for me to write unto you, and exhort [you] that ye should earnestly contend for the faith which was once delivered unto the saints."
    )


def test_chapterless_range_reference_found():
    """Test reference of the form BOOK VERSE_START-VERSE_END."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "Jude 3-4")
    assert (
        result
        == "3. Beloved, when I gave all diligence to write unto you of the common salvation, it was needful for me to write unto you, and exhort [you] that ye should earnestly contend for the faith which was once delivered unto the saints. 4. For there are certain men crept in unawares, who were before of old ordained to this condemnation, ungodly men, turning the grace of our God into lasciviousness, and denying the only Lord God, and our Lord Jesus Christ."
    )


def test_chapterless_book_reference_found():
    """Test single chapter book reference of the form BOOK."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "Jude")
    assert len(result) > 0


def test_process_schedule_data():
    """Test processing schedule data for a date."""
    # Create test schedule DataFrame
    data = {
        "Date": ["2024-02-18"],
        "Hymn 1": ["Hymn 290 - Hallelujah, Praise Jehovah"],
        "Scripture 0": ["Acts 2:34-35"],
        "Question": ["Q50. What is required in the second commandment?"],
        "Answer": [
            "A. The second commandment requireth the receiving, observing, and keeping pure and entire, all such religious worship and ordinances as God hath appointed in his Word."
        ],
    }
    schedule = pd.DataFrame(data)

    date = pd.to_datetime("2024-02-18").date()
    result = process_schedule_data(schedule, date)

    assert result["DATE"] == "2024-02-18"
    assert result["FORMATTED_DATE"] == "Sunday, February 18, 2024"
    assert result["HYMNS"] == "Hymn 290 - Hallelujah, Praise Jehovah"
    assert result["SCRIPTURES"] == "Acts 2:34-35"
    assert (
        result["CATECHISM_QUESTION"]
        == "Q50. What is required in the second commandment?"
    )
    assert (
        result["CATECHISM_ANSWER"]
        == "A. The second commandment requireth the receiving, observing, and keeping pure and entire, all such religious worship and ordinances as God hath appointed in his Word."
    )


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
