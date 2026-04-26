package org.trc.liturgist.scripture

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.nio.file.Path
import java.util.regex.Pattern
import kotlin.io.path.readText

@Serializable
data class BibleData(
    val version: String = "",
    @SerialName("version_display_name") val versionDisplayName: String = "",
    val books: List<BibleBook>
)

@Serializable
data class BibleBook(val name: String, val chapters: List<BibleChapter>)

@Serializable
data class BibleChapter(val verses: List<String>)

object ScriptureLookup {

    private val json = Json { ignoreUnknownKeys = true }

    fun loadBibleData(path: Path): BibleData {
        return json.decodeFromString(path.readText())
    }

    fun getScriptureText(bible: BibleData, passage: String): String {
        val result = StringBuilder()

        // Broad pattern to find book references — matches "Book Chapter:Verses" spans
        val broadPattern = Pattern.compile(
            """(?<book>(?:[1-3]\s)?[A-Za-z]+(?:\s[A-Za-z]+)*)\s*\d*(?:\s*:\s*\d+(?:\s*-\s*\d+)?|(?:\s*-\s*\d+))?"""
        )
        val matcher = broadPattern.matcher(passage)
        val matches = mutableListOf<String>()
        while (matcher.find()) {
            matches.add(matcher.group())
        }

        for ((matchIndex, matchText) in matches.withIndex()) {
            // Extract book name from match
            val bookMatcher = Pattern.compile(
                """(?<book>(?:[1-3]\s)?[A-Za-z]+(?:\s[A-Za-z]+)*)"""
            ).matcher(matchText)
            if (!bookMatcher.find()) continue
            val matchBook = bookMatcher.group("book")

            val book = bible.books.find { it.name == matchBook }
            if (book == null) {
                System.err.println("Cannot find book $matchBook")
                break
            }

            val chapters = book.chapters
            val verses: List<String>

            if (chapters.size == 1) {
                // Single-chapter book: refs like "Jude 3" or "Jude 3-4" (no chapter number)
                val versePattern = Pattern.compile(
                    """[1-3]?\s?[A-Za-z]+(?:\s[A-Za-z]+)*(?:\s*1:)?(?<start>\s*\d+)?(?:\s*-\s*(?<end>\d+))?"""
                )
                val pm = versePattern.matcher(matchText)
                val preciseMatch = if (pm.find()) pm else null

                val startStr = preciseMatch?.group("start")?.trim()
                val endStr = preciseMatch?.group("end")?.trim()

                val chapter = chapters[0]
                verses = if (startStr != null) {
                    val startIdx = startStr.toInt() - 1
                    val endIdx = if (endStr != null) endStr.toInt() else startStr.toInt()
                    val selected = chapter.verses.subList(startIdx, endIdx)
                    if (selected.size == 1) {
                        listOf(selected[0])
                    } else {
                        selected.mapIndexed { idx, verse -> "${idx + 1 + startIdx}. $verse" }
                    }
                } else {
                    chapter.verses.mapIndexed { idx, verse -> "${idx + 1}. $verse" }
                }
            } else {
                // Multi-chapter book: refs like "John 3:16" or "John 3:16-17" or "John 3"
                val versePattern = Pattern.compile(
                    """[1-3]?\s?[A-Za-z ]+ (?<chapter>\d+)(?::(?<start>\d+)(?:-(?<end>\d+))?)?"""
                )
                val pm = versePattern.matcher(matchText)
                if (!pm.find()) {
                    verses = emptyList()
                } else {
                    val chapterNum = pm.group("chapter").toInt()
                    val startStr = pm.group("start")
                    val endStr = pm.group("end")

                    val chapter = chapters[chapterNum - 1]
                    verses = if (startStr != null) {
                        val startIdx = startStr.toInt() - 1
                        val endIdx = if (endStr != null) endStr.toInt() else startStr.toInt()
                        val selected = chapter.verses.subList(startIdx, endIdx)
                        if (selected.size == 1) {
                            listOf(selected[0])
                        } else {
                            selected.mapIndexed { idx, verse -> "${idx + 1 + startIdx}. $verse" }
                        }
                    } else {
                        chapter.verses.mapIndexed { idx, verse -> "${idx + 1}. $verse" }
                    }
                }
            }

            val joined = verses.joinToString(" ")
            if (matchIndex < matches.size - 1) {
                result.append(joined).append(" (...) ")
            } else {
                result.append(joined)
            }
        }

        return result.toString()
    }
}
