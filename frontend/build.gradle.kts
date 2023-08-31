plugins {
    id("base")
    id("org.sonarqube")
    id("com.github.node-gradle.node") version "3.5.0"
}

node {
    version.set("16.14.0")
    npmVersion.set("8.3.1")
    npmInstallCommand.set("ci")
    distBaseUrl.set("https://nodejs.org/dist")
    download.set(true)
}

tasks {
    val distDir = "dist"

    "npm_run_build" {
        inputs.dir("$projectDir/src")
        inputs.dir("$projectDir/public")
        inputs.file("$projectDir/package.json")
        inputs.file("$projectDir/package-lock.json")
        outputs.dir(buildDir)
    }

    build {
        dependsOn("npm_run_build")
        dependsOn(":backend:generateOpenApiClient")
    }

    create<Delete>("distClean") {
        delete(buildDir, distDir)
    }

    clean {
        doFirst {
            delete(buildDir, "node_modules", distDir)
        }
    }

    register("start") {
        dependsOn("npm_run_serve")
    }
    register("package") {
        dependsOn("npm_run_build")
    }
}