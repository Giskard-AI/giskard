pluginManagement {
    repositories {
        maven("https://repo.spring.io/milestone")
        gradlePluginPortal()
    }
    plugins {
        id("org.springframework.boot") version "${extra["springBootVersion"]}"
        id("com.google.cloud.tools.jib") version "${extra["jibPluginVersion"]}"
        id("com.gorylenko.gradle-git-properties") version "${extra["gitPropertiesPluginVersion"]}"
        id("org.liquibase.gradle") version "${extra["liquibasePluginVersion"]}"
        id("org.sonarqube") version "${extra["sonarqubePluginVersion"]}"
        id("io.spring.nohttp") version "${extra["noHttpCheckstyleVersion"]}"
        id("com.github.andygoossens.gradle-modernizer-plugin") version "${extra["modernizerPluginVersion"]}"
    }
}

rootProject.name = "giskard"
include(
    "giskard-server",
    "giskard-frontend",
    "giskard-client"
)
