plugins {
    id("base")
    id("org.sonarqube")
    id("com.github.node-gradle.node") version "3.5.0"
}

sonarqube {
    properties {
        property("sonar.sources", "src")
        property("sonar.exclusions", listOf("src/generated-sources/**", "src/plugins/**", "src/styles/font-awesome/**"))
        property("sonar.sourceEncoding", "UTF-8")
    }
}


node {
    version.set("16.14.0")
    npmVersion.set("8.3.1")
    npmInstallCommand.set("ci")
    distBaseUrl.set("https://nodejs.org/dist")
    download.set(true)
}

tasks {
    "npm_run_build" {
        inputs.dir("$projectDir/src")
        inputs.dir("$projectDir/public")
        inputs.file("$projectDir/package.json")
        inputs.file("$projectDir/package-lock.json")
        outputs.dir(buildDir)
    }
    build {
        dependsOn("npm_run_build")
    }
    clean {
        doFirst {
            delete("build", "node_modules", "dist")
        }
    }
}