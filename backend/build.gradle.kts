import java.text.SimpleDateFormat
import java.util.*

group = "ai.giskard"
description = "Giskard main java backend"

val MIN_JAVA_VERSION = 17
if (JavaVersion.current().majorVersion.toInt() < MIN_JAVA_VERSION) {
    throw GradleException("This build requires at least Java $MIN_JAVA_VERSION, version used: ${JavaVersion.current()}")
}
repositories {
    mavenCentral()
}
buildscript {
    repositories {
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("java")
    id("idea")
    id("jacoco")
    id("org.sonarqube")
    id("org.springframework.boot")
    id("io.spring.dependency-management") version "1.1.2"
    id("com.gorylenko.gradle-git-properties") version "2.4.0"
    id("io.freefair.lombok") version "6.5.0.3"
    id("org.liquibase.gradle") version "2.1.1"
    id("com.github.andygoossens.gradle-modernizer-plugin") version "1.6.2"
}


var profiles: String = ""
if (project.hasProperty("prod")) {
    profiles = "prod"
    if (project.hasProperty("no-liquibase")) {
        profiles += ",no-liquibase"
    }

    if (project.hasProperty("api-docs")) {
        profiles += ",api-docs"
    }

    springBoot {
        buildInfo()
    }
} else {
    profiles = "dev"
    if (project.hasProperty("no-liquibase")) {
        profiles += ",no-liquibase"
    }
    if (project.hasProperty("tls")) {
        profiles += ",tls"
    }

    springBoot {
        buildInfo {
            properties {
//                time = null
            }
        }
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
idea {
    module {
        excludeDirs.plusAssign(files("node_modules"))
        excludeDirs.plusAssign(files("bin"))
    }
}

configure<org.springframework.boot.gradle.dsl.SpringBootExtension> {
    mainClass.set("ai.giskard.GiskardApp")
}

modernizer {
    failOnViolations = true
    includeTestClasses = true
}
jacoco {
    toolVersion = "0.8.8"
}

if (!project.hasProperty("runList")) {
    project.ext["runList"] = "main"
}
liquibase {
    runList = project.ext["runList"]
    val today = SimpleDateFormat("yyyyMMddHHmmss").format(Date())
    val changeLogFile = "src/main/resources/config/liquibase/changelog/${today}_changelog.xml"

    activities.register("main") {
        this.arguments = mapOf(
            "driver" to "org.postgresql.Driver",
            "url" to System.getenv().getOrDefault("SPRING_LIQUIBASE_URL", "jdbc:postgresql://localhost:5432/postgres"),
            "username" to System.getenv().getOrDefault("POSTGRES_USER", "postgres"),
            "password" to System.getenv().getOrDefault("POSTGRES_PASSWORD", "y1QYbF2BtFUC"),
            "changeLogFile" to "src/main/resources/config/liquibase/master.xml",
            "defaultSchemaName" to "",
            "logLevel" to "info",
            "classpath" to "src/main/resources/",
            "excludeObjects" to "hibernate_sequence,HIBERNATE_SEQUENCE,sequence_generator"
        )
    }
    activities.register("h2") {
        this.arguments = mapOf(
            "url" to "jdbc:h2:$liquibaseH2db/db;TRACE_LEVEL_FILE=0",
            "changeLogFile" to "src/main/resources/config/liquibase/master.xml",
            "defaultSchemaName" to "",
            "logLevel" to "info",
            "classpath" to "src/main/resources/",
        )
    }
    activities.register("diffLog") {
        this.arguments = mapOf(
            "url" to "jdbc:h2:$liquibaseH2db/db",
            "referenceUrl" to "hibernate:spring:ai.giskard.domain?dialect=org.hibernate.dialect.PostgreSQLDialect&hibernate.physical_naming_strategy=org.hibernate.boot.model.naming.CamelCaseToUnderscoresNamingStrategy&hibernate.implicit_naming_strategy=org.springframework.boot.orm.jpa.hibernate.SpringImplicitNamingStrategy",
            "classpath" to "$buildDir/classes/java/main",
            "changeLogFile" to changeLogFile,
            "logLevel" to "info",
            "excludeObjects" to "hibernate_sequence,HIBERNATE_SEQUENCE,sequence_generator"
        )
    }
}
gitProperties {
    dateFormat = "yyyy-MM-dd'T'HH:mm:ssZ"
    failOnNoGitDirectory = false
    keys = listOf("git.branch", "git.commit.id.abbrev", "git.commit.id.describe", "git.commit.time")
}

val liquibaseHibernate6Version: String by project.extra.properties
val jaxbRuntimeVersion: String by project.extra.properties
val archunitJunit5Version: String by project.extra.properties
val springBootVersion: String by project.extra.properties
val mapstructVersion: String by project.extra.properties
val liquibaseH2db = file(".liquibase_h2_db")

dependencies {
    liquibaseRuntime(sourceSets.main.get().compileClasspath)

    annotationProcessor("org.mapstruct:mapstruct-processor:${mapstructVersion}")
    annotationProcessor("org.projectlombok:lombok")
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor:${springBootVersion}")
    compileOnly("org.mapstruct:mapstruct:${mapstructVersion}")
    compileOnly("org.projectlombok:lombok")
    developmentOnly("org.springframework.boot:spring-boot-devtools:${springBootVersion}")
    implementation("com.fasterxml.jackson.core:jackson-annotations")
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-hibernate6")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-hppc")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310")
    implementation("com.fasterxml.jackson.module:jackson-module-jaxb-annotations")
    implementation("com.github.blagerweij:liquibase-sessionlock:1.6.2")
    implementation("com.h2database:h2")
    implementation("com.zaxxer:HikariCP")
    implementation("commons-codec:commons-codec:1.15")
    implementation("commons-fileupload:commons-fileupload:1.4")
    implementation("commons-io:commons-io:2.11.0")
    implementation("io.dropwizard.metrics:metrics-core")
    implementation("io.jsonwebtoken:jjwt-api:0.11.5")
    implementation("io.micrometer:micrometer-registry-prometheus")
//    implementation("javax.annotation:javax.annotation-api")
//    implementation("javax.transaction:javax.transaction-api")
    implementation("org.apache.commons:commons-compress:1.21")
    implementation("org.apache.commons:commons-csv:1.10.0")
    implementation("org.apache.commons:commons-lang3")
    implementation("org.bouncycastle:bcprov-jdk15on:1.70")
    implementation("org.hibernate.validator:hibernate-validator")
//    implementation("org.hibernate:hibernate-core")
//    implementation("org.hibernate:hibernate-entitymanager")
    implementation("org.liquibase:liquibase-core")
    implementation("org.postgresql:postgresql")
    implementation("org.springdoc:springdoc-openapi-webmvc-core")
    implementation("org.springframework.boot:spring-boot-loader-tools")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-logging")
    implementation("org.springframework.boot:spring-boot-starter-mail")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-thymeleaf")
    implementation("org.springframework.boot:spring-boot-starter-tomcat")
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-websocket")
    implementation("org.springframework.security:spring-security-config")
    implementation("org.springframework.security:spring-security-data")
    implementation("org.springframework.security:spring-security-messaging")
    implementation("org.springframework.security:spring-security-web")
    implementation("org.testcontainers:postgresql:1.18.3")
    implementation("org.zalando:problem-spring-web-starter:0.27.0")
    implementation(files("$projectDir/src/main/resources/third-party/j2ts-api.jar"))
    implementation(group = "com.fasterxml.jackson.dataformat", name = "jackson-dataformat-yaml", version = "2.13.1")
    implementation(group = "com.github.luben", name = "zstd-jni", version = "1.5.2-3")
    implementation(group = "org.apache.commons", name = "commons-compress", version = "1.21")
    implementation(group = "org.springdoc", name = "springdoc-openapi-ui", version = "1.6.11")
    implementation(group = "tech.tablesaw", name = "tablesaw-core", version = "0.43.1")
    implementation(group = "tech.tablesaw", name = "tablesaw-json", version = "0.34.2")
    liquibaseRuntime("info.picocli:picocli:4.7.0")
    liquibaseRuntime("org.liquibase.ext:liquibase-hibernate6:${liquibaseHibernate6Version}")
    liquibaseRuntime("org.liquibase:liquibase-core")
    liquibaseRuntime("org.postgresql:postgresql:42.5.2")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.11.5")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.11.5")
    testImplementation("com.h2database:h2")
    testImplementation("com.tngtech.archunit:archunit-junit5-api:${archunitJunit5Version}")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.boot:spring-boot-test")
    testImplementation("org.springframework.security:spring-security-test")
    testRuntimeOnly("com.tngtech.archunit:archunit-junit5-engine:${archunitJunit5Version}")
////    annotationProcessor("org.hibernate:hibernate-jpamodelgen:${hibernateVersion}.Final")
}

tasks {
    withType<Test> {
        useJUnitPlatform()
        maxParallelForks = Runtime.getRuntime().availableProcessors()
    }

    test {
        finalizedBy(jacocoTestReport)
    }

    jacocoTestReport {
        dependsOn(test)
    }

    jacocoTestReport {
        classDirectories.setFrom(files(sourceSets.main.get().output.classesDirs))
        sourceDirectories.setFrom(files(sourceSets.main.get().java.srcDirs))

        reports {
            xml.required.set(true)
            html.required.set(false)
        }
    }

    bootRun {
        args = listOf()
    }

    test {
        exclude("**/*IT*", "**/*IntTest*")
        testLogging {
            events.add(org.gradle.api.tasks.testing.logging.TestLogEvent.FAILED)
            events.add(org.gradle.api.tasks.testing.logging.TestLogEvent.SKIPPED)
        }
        jvmArgs?.add("-Djava.security.egd=file:/dev/./urandom -Xmx256m")
        reports.html.required.set(false)
    }

    bootJar {
        archiveFileName.set("${archiveBaseName.get()}.${archiveExtension.get()}")
    }

    create<Test>("integrationTest") {
        description = "Execute integration tests."
        group = "verification"
        include("**/*IT*", "**/*IntTest*")
        testLogging {
            events = setOf(
                org.gradle.api.tasks.testing.logging.TestLogEvent.FAILED,
                org.gradle.api.tasks.testing.logging.TestLogEvent.SKIPPED
            )
        }
        jvmArgs?.add("-Djava.security.egd=file:/dev/./urandom -Xmx256m")
        if (project.hasProperty("testcontainers")) {
            environment = mapOf("spring.profiles.active" to "testcontainers")
        }
        reports.html.required.set(false)
    }

    create<TestReport>("testReport") {
        destinationDirectory.set(file("$buildDir/reports/tests"))
    }

    create<TestReport>("integrationTestReport") {
        destinationDirectory.set(file("$buildDir/reports/tests"))
        testResults.from("integrationTest")
    }

    create<Delete>("distClean") {
        delete(buildDir)
    }
    create<Delete>("deleteLiquibaseH2DB") {
        delete(liquibaseH2db)
    }

    create<GradleBuild>("liquibaseUpdateH2") {
        doFirst {
            delete(liquibaseH2db)
        }
        doLast {
            println("Created temporary H2 database: $liquibaseH2db")
        }

        startParameter.setExcludedTaskNames(setOf("test", "integrationTest"))
        startParameter.projectProperties = mapOf("runList" to "h2")
        tasks = listOf("liquibaseUpdate")
    }

    create<GradleBuild>("liquibaseCreateDiff") {
        dependsOn("compileJava")
        startParameter.setExcludedTaskNames(setOf("test", "integrationTest"))
        startParameter.projectProperties = mapOf("runList" to "diffLog")

        tasks = listOf("liquibaseUpdateH2", "liquibaseDiffChangelog")

        doLast {
            delete(liquibaseH2db)
        }
    }

    create<Delete>("cleanResources") {
        delete = setOf("build/resources")
    }

    clean {
        dependsOn("distClean")
    }

    register("start") {
        dependsOn("bootRun")
    }
    register("package") {
        dependsOn("bootJar")
    }
}

defaultTasks("bootRun")








