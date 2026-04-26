package org.trc.liturgist.render

import com.github.jknack.handlebars.Handlebars
import com.github.jknack.handlebars.Template
import com.openhtmltopdf.extend.FSStream
import com.openhtmltopdf.pdfboxout.PdfRendererBuilder
import java.io.InputStream
import java.io.InputStreamReader
import java.io.Reader
import java.net.URL
import java.nio.file.Path
import kotlin.io.path.createDirectories
import kotlin.io.path.createTempFile
import kotlin.io.path.extension
import kotlin.io.path.outputStream
import kotlin.io.path.readText
import kotlin.io.path.writeText

object Renderer {

    fun loadTemplate(path: Path): Template {
        val source = path.readText(Charsets.UTF_8)
        return Handlebars().compileInline(source)
    }

    fun renderPdf(html: String, outputPath: Path) {
        outputPath.parent?.createDirectories()
        PdfRendererBuilder().apply {
            useFastMode()
            withHtmlContent(html, "")
            useHttpStreamImplementation { uri ->
                object : FSStream {
                    override fun getStream(): InputStream = URL(uri).openStream()
                    override fun getReader(): Reader = InputStreamReader(URL(uri).openStream())
                }
            }
            toStream(outputPath.outputStream())
        }.run()
    }

    fun renderViaPandoc(content: String, fromFmt: String, outputPath: Path) {
        outputPath.parent?.createDirectories()
        val tempInput = kotlin.io.path.createTempFile("liturgist-pandoc-", ".$fromFmt")
        try {
            tempInput.writeText(content)
            val process = ProcessBuilder(
                "pandoc",
                "--from=$fromFmt",
                "--to=${outputPath.extension}",
                "--output=${outputPath.toAbsolutePath()}",
                tempInput.toAbsolutePath().toString()
            ).redirectErrorStream(true).start()
            val exitCode = process.waitFor()
            if (exitCode != 0) {
                val output = process.inputStream.bufferedReader().readText()
                throw RuntimeException("pandoc failed (exit $exitCode): $output")
            }
        } finally {
            tempInput.toFile().delete()
        }
    }

    fun renderOutput(content: String, outputPath: Path, templatePath: Path? = null) {
        outputPath.parent?.createDirectories()
        when (outputPath.extension.lowercase()) {
            "pdf" -> renderPdf(content, outputPath)
            "docx", "odt" -> {
                val fromFmt = templatePath?.extension?.lowercase() ?: "html"
                renderViaPandoc(content, fromFmt, outputPath)
            }
            else -> outputPath.writeText(content, Charsets.UTF_8)
        }
    }
}
