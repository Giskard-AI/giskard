import com.google.protobuf.gradle.*
import org.gradle.api.JavaVersion
import java.text.SimpleDateFormat
import java.util.*

val MIN_JAVA_VERSION = 17
if (JavaVersion.current().majorVersion.toInt() < MIN_JAVA_VERSION) {
    throw GradleException("This build requires at least Java $MIN_JAVA_VERSION, version used: ${JavaVersion.current()}")
}

buildscript {
    repositories {
        gradlePluginPortal()
    }
}

plugins {
    id("java")
    id("idea")
    id("jacoco")
    id("org.springframework.boot")
    id("org.sonarqube")
    id("com.gorylenko.gradle-git-properties") version "2.4.0"
    id("io.freefair.lombok") version "6.6.1"
    id("org.liquibase.gradle") version "2.1.1"
    id("com.github.andygoossens.gradle-modernizer-plugin") version "1.6.2"
    id("com.google.protobuf") version "0.8.18"
}

group = "ai.giskard"
description = "Giskard main java backend"

defaultTasks("bootRun")

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
                time = null
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
            "url" to System.getenv().getOrDefault("SPRING_LIQUIBASE_URL", "jdbc:postgresql://localhost:5432/app"),
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
            "referenceUrl" to "hibernate:spring:ai.giskard.domain?dialect=tech.jhipster.domain.util.FixedPostgreSQL10Dialect&hibernate.physical_naming_strategy=org.springframework.boot.orm.jpa.hibernate.SpringPhysicalNamingStrategy&hibernate.implicit_naming_strategy=org.springframework.boot.orm.jpa.hibernate.SpringImplicitNamingStrategy",
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
repositories {
    mavenCentral()
}

val grpcVersion: String by project.extra.properties
val jhipsterDependenciesVersion: String by project.extra.properties
val liquibaseHibernate5Version: String by project.extra.properties
val jaxbRuntimeVersion: String by project.extra.properties
val archunitJunit5Version: String by project.extra.properties
val springBootVersion: String by project.extra.properties
val mapstructVersion: String by project.extra.properties
val liquibaseH2db = file(".liquibase_h2_db")

dependencies {
    implementation("io.grpc:grpc-netty:$grpcVersion")
    implementation("io.grpc:grpc-census:$grpcVersion")
    implementation("io.grpc:grpc-protobuf:$grpcVersion")
    implementation("io.grpc:grpc-stub:$grpcVersion")
    testImplementation("io.grpc:grpc-testing:$grpcVersion")

    implementation(platform("tech.jhipster:jhipster-dependencies:${jhipsterDependenciesVersion}"))
    implementation(group = "tech.jhipster", name = "jhipster-framework")
    implementation("javax.annotation:javax.annotation-api")
    implementation("io.dropwizard.metrics:metrics-core")
    implementation("io.micrometer:micrometer-registry-prometheus")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-hppc")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310")
    implementation("com.fasterxml.jackson.module:jackson-module-jaxb-annotations")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-hibernate5")
    implementation("com.fasterxml.jackson.core:jackson-annotations")
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("org.hibernate:hibernate-core")
    implementation("com.zaxxer:HikariCP")
    implementation("org.apache.commons:commons-lang3")
    implementation("javax.transaction:javax.transaction-api")
    implementation("org.hibernate:hibernate-entitymanager")
    implementation("org.hibernate.validator:hibernate-validator")
    implementation("org.liquibase:liquibase-core")

    liquibaseRuntime("org.liquibase:liquibase-core")
    liquibaseRuntime("org.liquibase.ext:liquibase-hibernate5:${liquibaseHibernate5Version}")
    liquibaseRuntime("org.postgresql:postgresql:42.5.0")
//    liquibaseRuntime("info.picocli:picocli:4.7.0")
    liquibaseRuntime(sourceSets.main.get().compileClasspath)

    implementation("org.springframework.boot:spring-boot-loader-tools")

    implementation("org.springframework.boot:spring-boot-starter-mail")
    implementation("org.springframework.boot:spring-boot-starter-logging")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    testImplementation("org.testcontainers:postgresql")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-web") {
        exclude(module = "spring-boot-starter-tomcat")
    }
    implementation("org.springframework.boot:spring-boot-starter-undertow")
    implementation("org.springframework.boot:spring-boot-starter-thymeleaf")
    implementation("org.zalando:problem-spring-web")
    implementation("org.springframework.cloud:spring-cloud-starter-bootstrap")
    implementation("org.springframework.security:spring-security-config")
    implementation("org.springframework.security:spring-security-data")
    implementation("org.springframework.security:spring-security-web")
    implementation("io.jsonwebtoken:jjwt-api")
    implementation(group = "tech.tablesaw", name = "tablesaw-core", version = "0.43.1")
    implementation(group = "tech.tablesaw", name = "tablesaw-json", version = "0.34.2")
    implementation(group = "org.apache.commons", name = "commons-compress", version = "1.21")
    runtimeOnly("io.jsonwebtoken:jjwt-impl")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson")

    implementation("org.springdoc:springdoc-openapi-webmvc-core")
    implementation(group = "org.springdoc", name = "springdoc-openapi-ui", version = "1.6.11")
    implementation("org.postgresql:postgresql")

    implementation("com.h2database:h2")
    testImplementation("com.h2database:h2")

//    annotationProcessor("org.hibernate:hibernate-jpamodelgen:${hibernateVersion}.Final")
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor:${springBootVersion}")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation("org.springframework.boot:spring-boot-test")
    testImplementation("com.tngtech.archunit:archunit-junit5-api:${archunitJunit5Version}")
    testRuntimeOnly("com.tngtech.archunit:archunit-junit5-engine:${archunitJunit5Version}")
    developmentOnly("org.springframework.boot:spring-boot-devtools:${springBootVersion}")
    protobuf(files("../common/proto"))

    compileOnly("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")
    // MapStruct
    compileOnly("org.mapstruct:mapstruct:${mapstructVersion}")
    annotationProcessor("org.mapstruct:mapstruct-processor:${mapstructVersion}")

    implementation(files("$projectDir/src/main/resources/third-party/j2ts-api.jar"))
    implementation(group = "com.fasterxml.jackson.dataformat", name = "jackson-dataformat-yaml", version = "2.13.3")
    implementation(group = "com.github.luben", name = "zstd-jni", version = "1.5.2-3")
    implementation("org.apache.commons:commons-compress:1.21")

    implementation("commons-codec:commons-codec:1.15")
    implementation("com.google.protobuf:protobuf-java-util:3.21.9")
    implementation("com.github.blagerweij:liquibase-sessionlock:1.6.0")
}

protobuf {
    val protocVersion by project.extra.properties

    protoc { artifact = "com.google.protobuf:protoc:${protocVersion}" }
    plugins {
        id("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:${grpcVersion}"
        }
    }
    generateProtoTasks {
        all().forEach {
            it.plugins {
                id("grpc")
            }
            it.doFirst {
                delete(it.outputBaseDir)
            }
        }
    }
}

sourceSets {
    main {
        java {
            srcDirs.add(file("build/generated/source/proto/main/grpc"))
            srcDirs.add(file("build/generated/source/proto/main/java"))
            srcDirs.add(file("build/generated/source/proto/main/python"))
        }
    }
}

tasks {
    withType<Test>() {
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

    create<Delete>("cleanGenerated") {
        delete = setOf(
            "$buildDir/extracted-include-protos",
            "$buildDir/extracted-protos",
            "$buildDir/proto",
            "$buildDir/generated/source/proto"
        )
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
}







