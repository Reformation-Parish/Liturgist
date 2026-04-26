package org.trc.liturgist

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.condition.EnabledIf
import org.trc.liturgist.scripture.BibleBook
import org.trc.liturgist.scripture.BibleChapter
import org.trc.liturgist.scripture.BibleData
import org.trc.liturgist.scripture.ScriptureLookup
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ScriptureLookupTest {

    private fun emptyBible() = BibleData(books = emptyList())

    private fun kjvPath(): Path = Path.of("../samples/kjv.json")

    private fun kjvAvailable() = kjvPath().exists()

    private fun loadKjv() = ScriptureLookup.loadBibleData(kjvPath())

    @Test
    fun `getScriptureText returns empty string when book not found`() {
        val result = ScriptureLookup.getScriptureText(emptyBible(), "John 3:16")
        assertEquals("", result)
    }

    @Test
    fun `getScriptureText chapter-verse range reference`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "John 3:16-17")
        assertTrue(result.contains("16."))
        assertTrue(result.contains("17."))
        assertTrue(result.contains("For God so loved the world"))
    }

    @Test
    fun `getScriptureText single chapter-verse reference`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "John 3:16")
        assertTrue(result.contains("For God so loved the world"))
        assertTrue(!result.contains("16."), "Single verse should not be prefixed with verse number")
    }

    @Test
    fun `getScriptureText chapter reference returns all verses`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "John 3")
        assertTrue(result.length > 0)
        assertTrue(result.contains("1."))
    }

    @Test
    fun `getScriptureText single-chapter book verse reference`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "Jude 3")
        assertTrue(result.contains("earnestly contend for the faith"))
        assertTrue(!result.contains("3."), "Single verse should not be prefixed")
    }

    @Test
    fun `getScriptureText single-chapter book verse range`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "Jude 3-4")
        assertTrue(result.contains("3."))
        assertTrue(result.contains("4."))
        assertTrue(result.contains("earnestly contend for the faith"))
    }

    @Test
    fun `getScriptureText entire single-chapter book`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "Jude")
        assertTrue(result.length > 0)
    }

    @Test
    fun `getScriptureText multiple non-contiguous references`() {
        if (!kjvAvailable()) return
        val result = ScriptureLookup.getScriptureText(loadKjv(), "John 3:16-17 John 4:1")
        assertTrue(result.contains("(...) "))
        assertTrue(result.contains("For God so loved the world"))
    }
}
