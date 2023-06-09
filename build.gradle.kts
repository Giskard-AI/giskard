import java.util.*

fun Project.applySonarProperties() {
    if (file("sonar-project.properties").exists()) {
        val sonarProperties = Properties().apply {
            load(file("sonar-project.properties").reader())
        }

        sonarProperties.forEach { key, value ->
            sonar {
                properties {
                    property(key as String, value as String)
                }
            }
        }
        sonar {
            properties {
                property("sonar.projectVersion", version.toString())
                property("sonar.branch", "fix/cleanup-after-v2")
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


