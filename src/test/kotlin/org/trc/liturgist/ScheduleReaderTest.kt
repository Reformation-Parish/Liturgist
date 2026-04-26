package org.trc.liturgist

import org.jetbrains.kotlinx.dataframe.AnyFrame
import org.jetbrains.kotlinx.dataframe.api.dataFrameOf
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.io.TempDir
import org.trc.liturgist.schedule.ScheduleReader
import java.io.File
import java.nio.file.Path
import java.time.LocalDate
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ScheduleReaderTest {

    @Test
    fun `nextSunday returns a LocalDate`() {
        val result = ScheduleReader.nextSunday()
        assertNotNull(result)
    }

    @Test
    fun `readSchedule CSV skips first row and uses second as header`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText("Header Row\nDate,Hymn 1,Scripture 1\n2024-02-18,Hymn 290,Acts 2:34-35\n")
        val df = ScheduleReader.readSchedule(csv.toPath())
        assertTrue(df.columnNames().contains("Date"))
        assertTrue(df.columnNames().contains("Hymn 1"))
        assertTrue(df.columnNames().contains("Scripture 1"))
    }

    @Test
    fun `readSchedule throws on unsupported extension`(@TempDir tmp: Path) {
        val f = tmp.resolve("schedule.txt").toFile()
        f.writeText("stuff")
        assertThrows<IllegalArgumentException> {
            ScheduleReader.readSchedule(f.toPath())
        }
    }

    @Test
    fun `findColumn returns exact match`() {
        assertEquals("Scripture 1", ScheduleReader.findColumn("Scripture 1", listOf("Scripture 1", "Scripture 10")))
    }

    @Test
    fun `findColumn returns prefix match with non-digit suffix`() {
        val result = ScheduleReader.findColumn("Scripture 1", listOf("Scripture 1 - Call to Worship"))
        assertEquals("Scripture 1 - Call to Worship", result)
    }

    @Test
    fun `findColumn does not match longer number`() {
        // "Scripture 1" should NOT match "Scripture 10"
        val result = ScheduleReader.findColumn("Scripture 1", listOf("Scripture 10", "Scripture 2"))
        assertNull(result)
    }

    @Test
    fun `processScheduleData returns basic fields`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText(
            "Sections\n" +
            "Date,Hymn 1,Scripture 1,Question,Answer\n" +
            "2024-02-18,Hymn 290 - Hallelujah,Acts 2:34-35,Q50. What?,A. The answer.\n"
        )
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 18)
        val result = ScheduleReader.processScheduleData(df, date)

        assertEquals("2024-02-18", result["DATE"])
        assertEquals("Sunday, February 18, 2024", result["FORMATTED_DATE"])
        assertEquals(listOf("Hymn 290 - Hallelujah"), result["HYMNS"])
        assertEquals(listOf("Acts 2:34-35"), result["SCRIPTURE_REFS"])
        assertEquals("Q50. What?", result["CATECHISM_QUESTION"])
        assertEquals("A. The answer.", result["CATECHISM_ANSWER"])
    }

    @Test
    fun `processScheduleData throws when date not found`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText("Sections\nDate,Hymn 1\n2024-02-18,Hymn 290\n")
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 25)
        assertThrows<IllegalArgumentException> {
            ScheduleReader.processScheduleData(df, date)
        }
    }

    @Test
    fun `processScheduleData preserves gaps as null`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText("Sections\nDate,Scripture 1,Scripture 3\n2024-02-18,Genesis 1:1,John 3:16\n")
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 18)
        val result = ScheduleReader.processScheduleData(df, date)

        @Suppress("UNCHECKED_CAST")
        val refs = result["SCRIPTURE_REFS"] as List<Any?>
        assertEquals("Genesis 1:1", refs[0])
        assertNull(refs[1])
        assertEquals("John 3:16", refs[2])
    }

    @Test
    fun `processScheduleData builds array from numbered columns`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText("Sections\nDate,Scripture 1,Scripture 2,Scripture 3\n2024-02-18,Genesis 1:1,Psalm 23:1,John 3:16\n")
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 18)
        val result = ScheduleReader.processScheduleData(df, date)

        assertEquals(listOf("Genesis 1:1", "Psalm 23:1", "John 3:16"), result["SCRIPTURE_REFS"])
    }

    @Test
    fun `processScheduleData matches descriptive column headings`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText(
            "Sections\n" +
            "Date,Scripture 1 - Call to Worship,Scripture 2 - Prayer Verse\n" +
            "2024-02-18,Genesis 1:1,Psalm 23:1\n"
        )
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 18)
        val result = ScheduleReader.processScheduleData(df, date)

        assertEquals(listOf("Genesis 1:1", "Psalm 23:1"), result["SCRIPTURE_REFS"])
    }

    @Test
    fun `processScheduleData does not match Scripture 1 against Scripture 10`(@TempDir tmp: Path) {
        val csv = tmp.resolve("schedule.csv").toFile()
        csv.writeText("Sections\nDate,Scripture 1,Scripture 10\n2024-02-18,Genesis 1:1,Psalm 23:1\n")
        val df = ScheduleReader.readSchedule(csv.toPath())
        val date = LocalDate.of(2024, 2, 18)
        val result = ScheduleReader.processScheduleData(df, date)

        @Suppress("UNCHECKED_CAST")
        val refs = result["SCRIPTURE_REFS"] as List<Any?>
        assertEquals("Genesis 1:1", refs[0])
        assertEquals("Psalm 23:1", refs[9])
        assertTrue(refs.subList(1, 9).all { it == null })
    }
}
