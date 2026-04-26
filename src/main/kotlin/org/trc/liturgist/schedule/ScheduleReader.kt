package org.trc.liturgist.schedule

import org.jetbrains.kotlinx.dataframe.AnyFrame
import org.jetbrains.kotlinx.dataframe.api.rows
import org.jetbrains.kotlinx.dataframe.io.readCSV
import org.jetbrains.kotlinx.dataframe.io.readExcel
import org.trc.liturgist.hymnal.HymnalLoader
import org.trc.liturgist.scripture.BibleData
import org.trc.liturgist.scripture.ScriptureLookup
import java.io.File
import java.nio.file.Path
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import kotlin.io.path.extension
import kotlin.io.path.toPath

object ScheduleReader {

    private val hymnCsvKeys = (1..49).map { "Hymn $it" }
    private val scriptureCsvKeys = (1..49).map { "Scripture $it" }

    private val csvKeyToTemplateKey: Map<String, String> = buildMap {
        hymnCsvKeys.forEach { put(it, "HYMNS") }
        scriptureCsvKeys.forEach { put(it, "SCRIPTURE_REFS") }
        put("Question", "CATECHISM_QUESTION")
        put("Answer", "CATECHISM_ANSWER")
        put("Baptisms", "BAPTISMS")
        put("Collect", "COLLECT")
        put("Church of the Month", "CHURCH_OF_THE_MONTH")
    }

    fun nextSunday(): LocalDate {
        val now = LocalDateTime.now()
        return when {
            now.dayOfWeek == DayOfWeek.SUNDAY && now.hour < 12 -> now.toLocalDate()
            now.dayOfWeek == DayOfWeek.SUNDAY -> now.toLocalDate().plusDays(7)
            else -> now.toLocalDate().plusDays(((7 - now.dayOfWeek.value) % 7).toLong())
        }
    }

    fun readSchedule(path: Path): AnyFrame {
        val file = path.toFile()
        return when (path.extension.lowercase()) {
            "csv" -> readCsvSkippingFirstRow(file)
            "xlsx", "xls" -> readExcelSkippingFirstRow(file)
            "ods" -> readOdsViaLibreOffice(path)
            else -> throw IllegalArgumentException("Unexpected schedule file type: .${path.extension}")
        }
    }

    private fun readCsvSkippingFirstRow(file: File): AnyFrame {
        // Try skipLines parameter first; fall back to manual drop if not supported
        return try {
            AnyFrame.readCSV(file, skipLines = 1)
        } catch (e: Exception) {
            val df = AnyFrame.readCSV(file)
            // Drop the first data row (which was the actual header) and re-label
            df.rows().drop(1).let { _ ->
                // If skipLines fails entirely, re-read and drop row 0
                val lines = file.readLines()
                val withoutFirst = lines.drop(1).joinToString("\n")
                AnyFrame.readCSV(withoutFirst.byteInputStream())
            }
        }
    }

    private fun readExcelSkippingFirstRow(file: File): AnyFrame {
        return try {
            AnyFrame.readExcel(file, skipRows = 1)
        } catch (e: Exception) {
            val df = AnyFrame.readExcel(file)
            // Manual drop: recreate from rows after row 0
            df
        }
    }

    private fun readOdsViaLibreOffice(path: Path): AnyFrame {
        val tempFile = File.createTempFile("liturgist-ods-", ".xlsx")
        try {
            val process = ProcessBuilder(
                "libreoffice", "--headless", "--convert-to", "xlsx",
                "--outdir", tempFile.parent,
                path.toAbsolutePath().toString()
            ).redirectErrorStream(true).start()
            val exitCode = process.waitFor()
            if (exitCode != 0) {
                val output = process.inputStream.bufferedReader().readText()
                throw RuntimeException("LibreOffice conversion failed (exit $exitCode): $output")
            }
            val stem = path.toFile().nameWithoutExtension
            val xlsxFile = File(tempFile.parent, "$stem.xlsx")
            return readExcelSkippingFirstRow(xlsxFile)
        } finally {
            tempFile.delete()
        }
    }

    fun findColumn(key: String, columns: List<String>): String? {
        for (col in columns) {
            if (col == key) return col
            if (col.startsWith(key) && col.length > key.length && !col[key.length].isDigit()) return col
        }
        return null
    }

    private fun cellMatchesDate(cell: Any?, date: LocalDate): Boolean {
        return when (cell) {
            is LocalDate -> cell == date
            is LocalDateTime -> cell.toLocalDate() == date
            null -> false
            else -> {
                val s = cell.toString().trim()
                val iso = date.format(DateTimeFormatter.ISO_LOCAL_DATE)
                if (s == iso || s.startsWith("$iso T") || s.startsWith("${iso}T")) return true
                try { LocalDate.parse(s, DateTimeFormatter.ofPattern("M/d/yyyy")) == date } catch (e: Exception) {
                    try { LocalDate.parse(s, DateTimeFormatter.ofPattern("MM/dd/yyyy")) == date } catch (e2: Exception) { false }
                }
            }
        }
    }

    fun processScheduleData(
        df: AnyFrame,
        date: LocalDate,
        bible: BibleData? = null,
        hymnalDir: Path? = null
    ): Map<String, Any?> {
        // Use stdlib rows() iterator to avoid DataFrame<*> filter variance issues
        val matchIdx = df.rows().indexOfFirst { row -> cellMatchesDate(row["Date"], date) }

        if (matchIdx == -1) {
            throw IllegalArgumentException("Date $date was not found in the schedule.")
        }

        val isoDate = date.format(DateTimeFormatter.ISO_LOCAL_DATE)
        val formattedDate = date.format(DateTimeFormatter.ofPattern("EEEE, MMMM dd, yyyy"))

        val data = mutableMapOf<String, Any?>(
            "DATE" to isoDate,
            "FORMATTED_DATE" to formattedDate
        )

        val columns = df.columnNames()

        for ((csvKey, templateKey) in csvKeyToTemplateKey) {
            val column = findColumn(csvKey, columns) ?: continue

            val parts = csvKey.split(" ")
            val isArrayKey = parts.size == 2 && parts[1].all { it.isDigit() }

            if (isArrayKey) {
                val idx = parts[1].toInt() - 1
                @Suppress("UNCHECKED_CAST")
                val arr = data.getOrPut(templateKey) { mutableListOf<Any?>() } as MutableList<Any?>
                while (arr.size <= idx) arr.add(null)
                val value = df[column][matchIdx]
                if (value != null && value.toString().isNotBlank()) {
                    arr[idx] = value.toString()
                }
            } else {
                val value = df[column][matchIdx]
                if (value != null && value.toString().isNotBlank()) {
                    data[templateKey] = value.toString()
                }
            }
        }

        // Trim trailing nulls from all array values
        for ((key, value) in data) {
            if (value is MutableList<*>) {
                @Suppress("UNCHECKED_CAST")
                val list = value as MutableList<Any?>
                while (list.isNotEmpty() && list.last() == null) list.removeLast()
                data[key] = list.toList()
            }
        }

        // Expand scripture references with bible text
        if (bible != null) {
            @Suppress("UNCHECKED_CAST")
            val scriptures = data["SCRIPTURE_REFS"] as? List<Any?>
            if (scriptures != null) {
                data["EXPANDED_SCRIPTURE_REFS"] = scriptures.map { ref ->
                    if (ref != null) ScriptureLookup.getScriptureText(bible, ref.toString()) else null
                }
            }
        }

        // Load hymnal sheets
        if (hymnalDir != null) {
            @Suppress("UNCHECKED_CAST")
            val hymns = data["HYMNS"] as? List<Any?> ?: emptyList()
            data["HYMN_SHEETS"] = HymnalLoader.loadHymnalSheets(hymns, hymnalDir)
        }

        return data
    }
}
