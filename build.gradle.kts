import java.util.*

fun Project.applySonarProperties() {
    if (file("sonar-project.properties").exists()) {
        val sonarProperties = Properties().apply {
            load(file("sonar-project.properties").reader())
        }

        sonarProperties.forEach { key, value ->
            sonarqube {
                properties {
                    property(key as String, value as String)
                }
            }
        }
        sonarqube {
            properties {
                property("sonar.projectVersion", version.toString())
            }
        }
    }
}
tasks.clean {
    delete(".gradle", "build")
}

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
    applySonarProperties()
}

applySonarProperties()


