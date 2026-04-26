# Port Liturgist to Kotlin

## Context

The Python Liturgist CLI generates liturgical service bulletins (PDF/DOCX/HTML) from a spreadsheet schedule. The goal is a Kotlin port in `liturgist-kt/` that replicates the full CLI and functionality with no Python runtime required.

Kotlin was chosen over Go because the JVM ecosystem solves two problems Go cannot: **OpenHTMLtoPDF** renders HTML→PDF in-process (no Chrome, no machine-level binary), and **Apache PDFBox** rasterizes PDF hymn sheets in-process (no mutool/pdftoppm). The remaining machine-level dependencies are pandoc (only for DOCX/ODT output) and LibreOffice (only for ODS input) — both optional features.

---

## Language Choice: Kotlin

| Concern | Kotlin/JVM | Go |
|---|---|---|
| HTML→PDF (no binary dep) | OpenHTMLtoPDF — pure JVM | None; Chrome shell-out required |
| PDF rasterization (no binary dep) | Apache PDFBox — pure JVM | None; mutool/pdftoppm shell-out required |
| XLSX/XLS reading | kotlinx.dataframe-excel (POI transitive) | excelize (pure Go) |
| ODS reading | LibreOffice shell-out | LibreOffice shell-out |
| Handlebars | handlebars.java — mature | raymond |
| JSON | kotlinx.serialization — idiomatic | encoding/json (stdlib) |
| CLI | Clikt — idiomatic Kotlin, no kapt | cobra |
| Distribution | Fat JAR (needs JRE) or GraalVM native | Single binary |
| JVM startup cost | ~200–400ms per invocation | ~10ms |

The startup cost is the main tradeoff. For a tool run occasionally to generate a bulletin, it's acceptable. The elimination of all machine-level dependencies for the core PDF path (generate + hymn rasterization) is the decisive advantage.

---

## Target Location

`liturgist-kt/` — a self-contained Gradle project, isolated from the Python source.

---

## Library Mapping

| Python dep | Kotlin replacement | Notes |
|---|---|---|
| `pandas` (CSV) | `org.jetbrains.kotlinx:dataframe-csv` | pandas-like API, `readCSV()` |
| `pandas` (XLSX/XLS) | `org.jetbrains.kotlinx:dataframe-excel` | `readExcel()`; POI is a transitive dep, not used directly |
| `odfpy` (ODS) | LibreOffice shell-out → temp XLSX | kotlinx.dataframe does not support ODS |
| `pybars3` | `com.github.jknack:handlebars` | Full `{{#each}}`, `{{#if}}`, `{{this}}` |
| `weasyprint` | `com.openhtmltopdf:openhtmltopdf-pdfbox` | Pure JVM, no binary required |
| `pymupdf` | `org.apache.pdfbox:pdfbox` | Pure JVM PDF rasterization |
| `pypandoc` | `pandoc` binary (shell-out) | Same approach as pypandoc-binary |
| `json` | `org.jetbrains.kotlinx:kotlinx-serialization-json` | For BibleData structs + `--print-json` output |
| `argparse` | `com.github.ajalt.clikt:clikt` | Kotlin-first, property delegates, no kapt |

---

## Project Structure

```
liturgist-kt/
├── build.gradle.kts
├── settings.gradle.kts
├── src/
│   └── main/
│       └── kotlin/org/trc/liturgist/
│           ├── Main.kt                     # entry point: LiturgistCommand().main(args)
│           ├── cli/
│           │   └── LiturgistCommand.kt     # CliktCommand with all flags, orchestration
│           ├── schedule/
│           │   └── ScheduleReader.kt       # readSchedule, findColumn, processScheduleData, nextSunday
│           ├── scripture/
│           │   └── ScriptureLookup.kt      # BibleData @Serializable, getScriptureText
│           ├── hymnal/
│           │   └── HymnalLoader.kt         # parseHymnNumber, loadHymnImages, loadHymnalSheets
│           └── render/
│               └── Renderer.kt             # loadTemplate, renderOutput (PDF/DOCX/ODT/plain)
│   └── test/
│       └── kotlin/org/trc/liturgist/
│           ├── ScheduleReaderTest.kt
│           ├── ScriptureLookupTest.kt
│           └── HymnalLoaderTest.kt
└── README.md
```

---

## build.gradle.kts

```kotlin
plugins {
    kotlin("jvm") version "2.0.0"
    kotlin("plugin.serialization") version "2.0.0"
    id("com.github.johnrengelman.shadow") version "8.1.1"
    application
}

application {
    mainClass.set("org.trc.liturgist.MainKt")
}

dependencies {
    implementation("com.github.ajalt.clikt:clikt:4.4.0")

    implementation("com.github.jknack:handlebars:4.3.1")
    implementation("org.jetbrains.kotlinx:dataframe:1.0.0-Beta4")
    implementation("org.jetbrains.kotlinx:dataframe-excel:1.0.0-Beta4")

    implementation("com.openhtmltopdf:openhtmltopdf-pdfbox:1.0.10")
    implementation("org.apache.pdfbox:pdfbox:3.0.2")

    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}
```

Distribution: `./gradlew shadowJar` produces `build/libs/liturgist-kt-all.jar`. Run as `java -jar liturgist-kt-all.jar`. Optionally wrap in a shell script named `liturgist`. GraalVM native image is possible via the `org.graalvm.buildtools.native` Gradle plugin but requires additional reflection config.

---

## Critical Implementation Details

### CSV/XLSX row-skip logic
`pd.read_csv(path, header=1)` skips row 0 (section titles) and uses row 1 as column names. With kotlinx.dataframe:
```kotlin
// CSV: skipLines skips rows before the header row
val df = DataFrame.readCSV(path.toFile(), skipLines = 1)

// XLSX/XLS: skipRows works the same way
val df = DataFrame.readExcel(path.toFile(), skipRows = 1)
```
The exact parameter names (`skipLines`, `skipRows`) should be verified against the KDocs — the documentation is sparse at Beta4. If they don't exist, read without skipping and drop the first row manually before treating row 1 as column names.

### `findColumn` (ports `_find_column`, `core.py:168-179`)
```kotlin
fun findColumn(key: String, columns: List<String>): String? {
    for (col in columns) {
        if (col == key) return col
        if (col.startsWith(key) && col.length > key.length && !col[key.length].isDigit()) return col
    }
    return null
}
```

### `nextSunday` (ports `core.py:31-43`)
Java's `DayOfWeek` is ISO-8601: Mon=1…Sun=7. Python's `weekday()` is Mon=0…Sun=6.
```kotlin
fun nextSunday(): LocalDate {
    val now = LocalDateTime.now()
    return when {
        now.dayOfWeek == DayOfWeek.SUNDAY && now.hour < 12 -> now.toLocalDate()
        now.dayOfWeek == DayOfWeek.SUNDAY -> now.toLocalDate().plusDays(7)
        else -> now.toLocalDate().plusDays(((7 - now.dayOfWeek.value) % 7).toLong())
    }
}
```

### Array gap preservation (`core.py:228-253`)
Build `MutableList<Any?>` of size up to 49 with nulls. Insert values at `index - 1`. Trim trailing nulls. Pass as `List<Any?>` to handlebars.java (it treats `null` entries as empty string in `{{#each}}`).

### BibleData structs (kotlinx.serialization)
```kotlin
@Serializable
data class BibleData(
    val version: String = "",
    @SerialName("version_display_name") val versionDisplayName: String = "",
    val books: List<BibleBook>
)
@Serializable data class BibleBook(val name: String, val chapters: List<BibleChapter>)
@Serializable data class BibleChapter(val verses: List<String>)
```
Load: `Json.decodeFromString<BibleData>(File(path).readText())`

### `--print-json` output (kotlinx.serialization)
Template data is `Map<String, Any?>`. Convert to `JsonElement` recursively, then pretty-print:
```kotlin
fun anyToJson(value: Any?): JsonElement = when (value) {
    null -> JsonNull
    is String -> JsonPrimitive(value)
    is List<*> -> JsonArray(value.map { anyToJson(it) })
    else -> JsonPrimitive(value.toString())
}
val json = Json { prettyPrint = true }
println(json.encodeToString(JsonObject(data.mapValues { anyToJson(it.value) })))
```

### Scripture reference parsing (`core.py:101-165`)
Java `Pattern`/`Matcher` replaces Python `re.finditer`. The named-group syntax `(?P<name>...)` becomes `(?<name>...)` in Java regex. The two-pass iterator pattern:
```kotlin
val matcher = broadPattern.matcher(passage)
val matches = mutableListOf<MatchResult>()
while (matcher.find()) matches.add(...)
// Iterate with index to detect last match (for ` (...) ` separator)
```
Port all four reference forms from `core.py:117-123` with this syntax change.

### HTML→PDF with OpenHTMLtoPDF (`cli.py:78-79`)
```kotlin
fun renderPdf(html: String, outputPath: Path) {
    outputPath.parent.createDirectories()
    PdfRendererBuilder().apply {
        useFastMode()
        withHtmlContent(html, "")
        useHttpStreamImplementation { uri -> URL(uri).openStream() }  // enables Google Fonts
        toStream(outputPath.outputStream())
    }.run()
}
```
`useHttpStreamImplementation` is required so Google Fonts load at render time. The existing templates reference `fonts.googleapis.com` — without it, fonts silently fall back to system defaults.

### PDF rasterization with PDFBox (`hymnal.py:29-37`)
```kotlin
fun rasterizePdf(pdfPath: Path, dpi: Float = 300f): List<String> {
    return PDDocument.load(pdfPath.toFile()).use { doc ->
        val renderer = PDFRenderer(doc)
        (0 until doc.numberOfPages).map { page ->
            val image = renderer.renderImageWithDPI(page, dpi, ImageType.RGB)
            val baos = ByteArrayOutputStream()
            ImageIO.write(image, "PNG", baos)
            "data:image/png;base64," + Base64.getEncoder().encodeToString(baos.toByteArray())
        }
    }
}
```

### `renderOutput` dispatch (`cli.py:61-100`)
- `.pdf` → `renderPdf(html, outputPath)`
- `.docx` / `.odt` → `renderViaPandoc(content, templateExt, outputPath)` (shell-out; pandoc `--from=<templateExt>`)
- anything else → `outputPath.writeText(content)`

### Date column handling with kotlinx.dataframe
`DataFrame.readExcel` and `readCSV` infer column types automatically. The Date column may come through as `LocalDate`, `LocalDateTime`, or `String` depending on the file. Filter robustly:
```kotlin
val week = df.filter {
    val cell = it["Date"]
    when (cell) {
        is LocalDate -> cell == date
        is LocalDateTime -> cell.toLocalDate() == date
        is String -> LocalDate.parse(cell, DateTimeFormatter.ofPattern("M/d/yyyy")) == date
        else -> false
    }
}
```

---

## Implementation Steps

### Phase 1: Scaffold
1. `liturgist-kt/settings.gradle.kts`, `build.gradle.kts` with all deps
2. `Main.kt`: `fun main(args: Array<String>) = LiturgistCommand().main(args)`
3. `LiturgistCommand.kt`: extend `CliktCommand`; declare all 6 options and positional `schedule` argument via property delegates; validate `--template` OR `--print-json` in `run()` with `fail()`
```kotlin
class LiturgistCommand : CliktCommand(name = "liturgist") {
    val schedule by argument(help = "Path to schedule file (CSV, XLSX, XLS, ODS)")
    val date by option("--date", help = "Date in YYYY-MM-DD format; defaults to next Sunday")
    val printJson by option("--print-json").flag()
    val bibleJsonPath by option("--bible-json-path")
    val template by option("--template")
    val outputPath by option("-o", "--output").default("output/out.pdf")
    val hymnalDir by option("--hymnal-dir")
    override fun run() {
        if (template == null && !printJson) fail("You must specify --template or --print-json.")
        // ...
    }
}
```

### Phase 2: `ScheduleReader.kt`
1. `nextSunday(): LocalDate`
2. `readSchedule(path: Path): AnyFrame` — dispatch on extension; CSV via `DataFrame.readCSV(skipLines=1)`; XLSX/XLS via `DataFrame.readExcel(skipRows=1)`; ODS via LibreOffice shell-out to temp XLSX then `readExcel`
3. `findColumn(key: String, columns: List<String>): String?`
4. `processScheduleData(df: AnyFrame, date: LocalDate, bibleJsonPath?, hymnalDir?): Map<String, Any?>` — filter with `df.filter { ... }`, access values via `df["ColumnName"][0]`

### Phase 3: `ScriptureLookup.kt`
1. `BibleData`, `BibleBook`, `BibleChapter` `@Serializable` data classes
2. `loadBibleData(path: Path): BibleData`
3. `getScriptureText(bible: BibleData, passage: String): String` — two-pass Java regex, ` (...) ` separator, single-chapter vs multi-chapter verse patterns

### Phase 4: `HymnalLoader.kt`
1. `parseHymnNumber(s: String): Int?` — `(?i)Hymn\s+(\d+)`
2. `rasterizePdf(path: Path): List<String>` — PDFBox, base64 data URIs
3. `loadHymnImages(num: Int, dir: Path): List<String>` — priority: `.pdf` → `rasterizePdf`; `-1.png, -2.png...`; `.png`
4. `loadHymnalSheets(hymns: List<Any?>, dir: Path): List<List<String>>`

### Phase 5: `Renderer.kt`
1. `loadTemplate(path: Path): Template` — `Handlebars().compile(reader)`
2. `renderPdf(html: String, outputPath: Path)` — OpenHTMLtoPDF with HTTP stream impl
3. `renderViaPandoc(content: String, fromFmt: String, outputPath: Path)` — `ProcessBuilder`
4. `renderOutput(content: String, outputPath: Path, templatePath: Path?)` — dispatch

### Phase 6: Wire + Tests
1. Connect all phases in `LiturgistCommand.run()`
2. Port test cases from `tests/test_core.py` and `tests/test_hymnal.py` as JUnit5 `@ParameterizedTest` / `@Test`
3. Integration test: `--print-json` output against Python golden output

---

## Critical Files to Reference During Implementation

- `src/liturgist/core.py` — schedule processing, scripture parsing, column matching
- `src/liturgist/hymnal.py` — image loading logic
- `src/liturgist/cli.py` — flags, validation, render dispatch
- `tests/test_core.py` — reference cases to port to Kotlin tests
- `samples/schedule.csv` — golden data for integration tests

---

## Verification

```bash
# Build fat JAR
cd liturgist-kt && ./gradlew shadowJar

# Unit tests
./gradlew test

# Functional parity check
java -jar build/libs/liturgist-kt-all.jar \
  ../samples/schedule.csv --date 2025-01-05 --print-json

# PDF generation (pure JVM, no Chrome needed)
java -jar build/libs/liturgist-kt-all.jar \
  ../samples/schedule.csv --date 2025-01-05 \
  --template ../samples/order-of-worship-sequential.html \
  --bible-json-path ../samples/kjv.json \
  -o /tmp/bulletin.pdf
```

---

## Risks & Mitigations

**OpenHTMLtoPDF CSS coverage.** It doesn't support CSS Grid or CSS custom properties. The sample templates use flexbox-style layouts and `@media print` — both supported. If a template uses Grid, it will fall back to block layout silently. Test against both sample templates before declaring parity.

**Google Fonts at render time.** `useHttpStreamImplementation` fetches fonts over HTTP during PDF rendering. If the machine is offline, fonts fall back silently. An offline-safe alternative: pre-download font files and rewrite `fonts.googleapis.com` URLs to local paths, or bundle the fonts in the template.

**handlebars.java with `null` in `List<Any?>`.**  Verify that `{{#each HYMNS}}{{this}}{{/each}}` renders null list slots as empty string (it does by default) and that `{{#if}}` on a null-containing list evaluates correctly.

**kotlinx.dataframe Beta status.** `1.0.0-Beta4` is pre-release software. API may change before 1.0 stable. The row-skip parameters (`skipLines`, `skipRows`) should be verified against KDocs before implementation — the public docs are thin. Pin the exact version in `build.gradle.kts` to avoid surprise breakage on resolution.

**XLS via dataframe-excel.** The `dataframe-excel` module uses Apache POI as a transitive dependency. Date cell handling in `.xls` (HSSF) may differ from `.xlsx` (XSSF). Test explicitly with an XLS fixture if XLS support is needed.

**ODS shell-out.** Requires LibreOffice. If absent: clear error message. CSV and XLSX work with zero external dependencies.

**DOCX/ODT shell-out.** Requires pandoc. If absent: clear error message. Only triggered when output extension is `.docx` or `.odt`.

**JVM startup time.** ~200–400ms cold start. Acceptable for occasional bulletin generation. Not suitable as an inner loop tool.
