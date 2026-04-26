package org.trc.liturgist.hymnal

import org.apache.pdfbox.Loader
import org.apache.pdfbox.rendering.ImageType
import org.apache.pdfbox.rendering.PDFRenderer
import java.io.ByteArrayOutputStream
import java.nio.file.Path
import java.util.Base64
import java.util.regex.Pattern
import javax.imageio.ImageIO
import kotlin.io.path.exists
import kotlin.io.path.readBytes

object HymnalLoader {

    private val hymnPattern = Pattern.compile("""(?i)Hymn\s+(\d+)""")

    fun parseHymnNumber(s: String): Int? {
        val matcher = hymnPattern.matcher(s)
        return if (matcher.find()) matcher.group(1).toInt() else null
    }

    fun rasterizePdf(pdfPath: Path, dpi: Float = 300f): List<String> {
        return Loader.loadPDF(pdfPath.toFile()).use { doc ->
            val renderer = PDFRenderer(doc)
            (0 until doc.numberOfPages).map { page ->
                val image = renderer.renderImageWithDPI(page, dpi, ImageType.RGB)
                val baos = ByteArrayOutputStream()
                ImageIO.write(image, "PNG", baos)
                "data:image/png;base64," + Base64.getEncoder().encodeToString(baos.toByteArray())
            }
        }
    }

    fun loadHymnImages(hymnNumber: Int, dir: Path): List<String> {
        // 1. PDF takes priority
        val pdfPath = dir.resolve("$hymnNumber.pdf")
        if (pdfPath.exists()) return rasterizePdf(pdfPath)

        // 2. Multi-page PNGs: {num}-1.png, {num}-2.png, ...
        val firstPage = dir.resolve("$hymnNumber-1.png")
        if (firstPage.exists()) {
            val pages = mutableListOf<String>()
            var pageNum = 1
            while (true) {
                val pagePath = dir.resolve("$hymnNumber-$pageNum.png")
                if (!pagePath.exists()) break
                pages.add(pngDataUri(pagePath.readBytes()))
                pageNum++
            }
            return pages
        }

        // 3. Single PNG
        val singlePage = dir.resolve("$hymnNumber.png")
        if (singlePage.exists()) return listOf(pngDataUri(singlePage.readBytes()))

        return emptyList()
    }

    fun loadHymnalSheets(hymns: List<Any?>, dir: Path): List<List<String>> {
        return hymns.map { hymnEntry ->
            val str = hymnEntry?.toString() ?: return@map emptyList()
            val number = parseHymnNumber(str)
            if (number != null) loadHymnImages(number, dir) else emptyList()
        }
    }

    private fun pngDataUri(bytes: ByteArray): String {
        return "data:image/png;base64," + Base64.getEncoder().encodeToString(bytes)
    }
}
