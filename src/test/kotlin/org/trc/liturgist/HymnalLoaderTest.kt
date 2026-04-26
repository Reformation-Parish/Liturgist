package org.trc.liturgist

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import org.trc.liturgist.hymnal.HymnalLoader
import java.nio.file.Path
import java.util.Base64
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

// Minimal valid 1x1 white PNG
private val TINY_PNG = byteArrayOf(
    0x89.toByte(), 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90.toByte(), 0x77, 0x53,
    0xDE.toByte(), 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x78, 0x9C.toByte(), 0x63, 0xF8.toByte(), 0x0F, 0x00, 0x00, 0x01,
    0x01, 0x00, 0x05, 0x18, 0xD8.toByte(), 0x4E, 0x00, 0x00,
    0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE.toByte(), 0x42,
    0x60, 0x82.toByte()
)

class HymnalLoaderTest {

    @Test
    fun `parseHymnNumber standard format`() {
        assertEquals(552, HymnalLoader.parseHymnNumber("Hymn 552 - Rejoice, All Ye Believers"))
    }

    @Test
    fun `parseHymnNumber single digit`() {
        assertEquals(1, HymnalLoader.parseHymnNumber("Hymn 1 - A Mighty Fortress"))
    }

    @Test
    fun `parseHymnNumber case insensitive`() {
        assertEquals(100, HymnalLoader.parseHymnNumber("hymn 100 - some title"))
    }

    @Test
    fun `parseHymnNumber no title`() {
        assertEquals(42, HymnalLoader.parseHymnNumber("Hymn 42"))
    }

    @Test
    fun `parseHymnNumber no match plain text`() {
        assertNull(HymnalLoader.parseHymnNumber("Opening Prayer"))
    }

    @Test
    fun `parseHymnNumber no match empty`() {
        assertNull(HymnalLoader.parseHymnNumber(""))
    }

    @Test
    fun `parseHymnNumber no match number only`() {
        assertNull(HymnalLoader.parseHymnNumber("552"))
    }

    @Test
    fun `loadHymnImages single png`(@TempDir tmp: Path) {
        tmp.resolve("100.png").toFile().writeBytes(TINY_PNG)
        val result = HymnalLoader.loadHymnImages(100, tmp)
        assertEquals(1, result.size)
        assertTrue(result[0].startsWith("data:image/png;base64,"))
        val b64 = result[0].removePrefix("data:image/png;base64,")
        assertTrue(Base64.getDecoder().decode(b64).contentEquals(TINY_PNG))
    }

    @Test
    fun `loadHymnImages multi-page pngs`(@TempDir tmp: Path) {
        tmp.resolve("552-1.png").toFile().writeBytes(TINY_PNG)
        tmp.resolve("552-2.png").toFile().writeBytes(TINY_PNG)
        tmp.resolve("552-3.png").toFile().writeBytes(TINY_PNG)
        val result = HymnalLoader.loadHymnImages(552, tmp)
        assertEquals(3, result.size)
        result.forEach { assertTrue(it.startsWith("data:image/png;base64,")) }
    }

    @Test
    fun `loadHymnImages multi-page preferred over single`(@TempDir tmp: Path) {
        tmp.resolve("552.png").toFile().writeBytes(TINY_PNG)
        tmp.resolve("552-1.png").toFile().writeBytes(TINY_PNG)
        tmp.resolve("552-2.png").toFile().writeBytes(TINY_PNG)
        val result = HymnalLoader.loadHymnImages(552, tmp)
        assertEquals(2, result.size)
    }

    @Test
    fun `loadHymnImages missing returns empty`(@TempDir tmp: Path) {
        val result = HymnalLoader.loadHymnImages(999, tmp)
        assertEquals(emptyList(), result)
    }

    @Test
    fun `loadHymnalSheets list input`(@TempDir tmp: Path) {
        tmp.resolve("552.png").toFile().writeBytes(TINY_PNG)
        val hymns = listOf("Hymn 552 - Rejoice, All Ye Believers", "Hymn 999 - Does Not Exist")
        val result = HymnalLoader.loadHymnalSheets(hymns, tmp)
        assertEquals(2, result.size)
        assertEquals(1, result[0].size)
        assertEquals(emptyList(), result[1])
    }

    @Test
    fun `loadHymnalSheets no hymn number returns empty inner list`(@TempDir tmp: Path) {
        val result = HymnalLoader.loadHymnalSheets(listOf("Doxology"), tmp)
        assertEquals(listOf(emptyList<String>()), result)
    }

    @Test
    fun `loadHymnalSheets empty list`(@TempDir tmp: Path) {
        val result = HymnalLoader.loadHymnalSheets(emptyList(), tmp)
        assertEquals(emptyList(), result)
    }
}
