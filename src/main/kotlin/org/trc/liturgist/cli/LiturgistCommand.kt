package org.trc.liturgist.cli

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.UsageError
import com.github.ajalt.clikt.parameters.arguments.argument
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option
import kotlinx.serialization.json.*
import org.trc.liturgist.hymnal.HymnalLoader
import org.trc.liturgist.render.Renderer
import org.trc.liturgist.schedule.ScheduleReader
import org.trc.liturgist.scripture.ScriptureLookup
import java.nio.file.Path
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlin.io.path.Path

class LiturgistCommand : CliktCommand(name = "liturgist", help = "A liturgical document generator") {
    val schedule by argument(help = "Path to schedule file (CSV, XLSX, XLS, ODS)")
    val date by option("--date", help = "Date in YYYY-MM-DD format; defaults to next Sunday")
    val printJson by option("--print-json", help = "Print selected data as JSON").flag()
    val bibleJsonPath by option("--bible-json-path", help = "A file containing the verses in JSON arrays")
    val template by option("--template", help = "A path to a Handlebars template")
    val outputPath by option("-o", "--output", help = "A path to the output file").default("output/out.pdf")
    val hymnalDir by option("--hymnal-dir", help = "Directory containing hymn sheet music files named by number")

    override fun run() {
        if (template == null && !printJson) {
            throw UsageError("You must specify --template or --print-json.")
        }

        val resolvedDate: LocalDate = if (date != null) {
            try {
                LocalDate.parse(date, DateTimeFormatter.ISO_LOCAL_DATE)
            } catch (e: Exception) {
                throw UsageError("Error parsing date '$date': ${e.message}")
            }
        } else {
            ScheduleReader.nextSunday()
        }

        val schedulePath = Path(schedule)
        val df = try {
            ScheduleReader.readSchedule(schedulePath)
        } catch (e: Exception) {
            throw UsageError("Error reading schedule: ${e.message}")
        }

        val bible = if (bibleJsonPath != null) ScriptureLookup.loadBibleData(Path(bibleJsonPath!!)) else null
        val hymnDir = if (hymnalDir != null) Path(hymnalDir!!) else null

        val data = try {
            ScheduleReader.processScheduleData(df, resolvedDate, bible, hymnDir)
        } catch (e: IllegalArgumentException) {
            throw UsageError(e.message ?: "Error processing schedule data")
        } catch (e: Exception) {
            throw UsageError("Error processing schedule data: ${e.message}")
        }

        if (printJson) {
            val json = Json { prettyPrint = true }
            println(json.encodeToString(JsonElement.serializer(), JsonObject(data.mapValues { anyToJson(it.value) })))
        }

        if (template != null) {
            val templatePath = Path(template!!)
            val tmpl = try {
                Renderer.loadTemplate(templatePath)
            } catch (e: Exception) {
                throw UsageError("Unable to open template file: $templatePath")
            }

            val renderedContent = tmpl.apply(data)
            try {
                Renderer.renderOutput(renderedContent, Path(outputPath), templatePath)
                System.err.println("$outputPath generated successfully")
            } catch (e: Exception) {
                throw UsageError("Error rendering template: ${e.message}")
            }
        }
    }

    private fun anyToJson(value: Any?): JsonElement = when (value) {
        null -> JsonNull
        is String -> JsonPrimitive(value)
        is Boolean -> JsonPrimitive(value)
        is Number -> JsonPrimitive(value)
        is List<*> -> JsonArray(value.map { anyToJson(it) })
        is Map<*, *> -> JsonObject(value.entries.associate { (k, v) -> k.toString() to anyToJson(v) })
        else -> JsonPrimitive(value.toString())
    }
}
