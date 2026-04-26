plugins {
    kotlin("jvm") version "2.0.0"
    kotlin("plugin.serialization") version "2.0.0"
    id("com.gradleup.shadow") version "8.3.6"
    application
}

group = "org.trc"
version = "1.0.0"

application {
    mainClass.set("org.trc.liturgist.MainKt")
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.github.ajalt.clikt:clikt:4.4.0")

    implementation("com.github.jknack:handlebars:4.3.1")
    implementation("org.jetbrains.kotlinx:dataframe:0.13.1")
    implementation("org.jetbrains.kotlinx:dataframe-excel:0.13.1")

    implementation("com.openhtmltopdf:openhtmltopdf-pdfbox:1.0.10")
    implementation("org.apache.pdfbox:pdfbox:3.0.2")

    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

tasks.test {
    useJUnitPlatform()
}

kotlin {
    jvmToolchain(17)
}

tasks.shadowJar {
    archiveBaseName.set("liturgist-kt")
    archiveClassifier.set("all")
    archiveVersion.set("")
    mergeServiceFiles()
    manifest {
        attributes["Main-Class"] = "org.trc.liturgist.MainKt"
    }
}
