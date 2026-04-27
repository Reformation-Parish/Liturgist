"""Tests for liturgist.scripture module."""

import json
from pathlib import Path

from liturgist.scripture import get_scripture_text


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
        == "16. ‹For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.› 17. ‹For God sent not his Son into the world to condemn the world; but that the world through him might be saved.› (...) When therefore the Lord knew how the Pharisees had heard that Jesus made and baptized more disciples than John,"
    )


def test_chapter_verse_reference_found():
    """Test full reference of the form BOOK CHAPTER:START."""
    json_path = Path("samples/kjv.json")
    bible_text = json_path.read_text(encoding="utf-8")
    bible_data = json.loads(bible_text)

    result = get_scripture_text(bible_data, "John 3:16")
    assert (
        result
        == "‹For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.›"
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
        == "Beloved, when I gave all diligence to write unto you of the common salvation, it was needful for me to write unto you, and exhort [you] that ye should earnestly contend for the faith which was once delivered unto the saints."
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
