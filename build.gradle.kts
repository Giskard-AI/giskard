plugins {
    id("base")
    id("org.sonarqube")
    `kotlin-dsl`
}

repositories {
    mavenCentral()
}

allprojects {
    version = extra["giskardVersion"]!!
}

sonarqube {
    properties {
        property("sonar.organization", "giskard")
        property("sonar.projectKey", "giskard")
        property("sonar.host.url", "https://sonarcloud.io")
        property("sonar.projectVersion", version.toString())
    }
}