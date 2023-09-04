import ru.vyarus.gradle.plugin.python.PythonExtension.Scope.VIRTUALENV
import ru.vyarus.gradle.plugin.python.task.PythonTask

plugins {
    id("base")
    id("idea")
    id("org.sonarqube")
    id("ru.vyarus.use-python") version "3.0.0"
}

tasks {
    val virtualEnvDirectory = ".venv"
    python {
        envPath = virtualEnvDirectory
        minPythonVersion = "3.8"
        scope = VIRTUALENV
        installVirtualenv = true
        pip(listOf("pdm:2.8.2", "urllib3:1.26.15", "certifi:2023.7.22"))
    }

    create<PythonTask>("install") {
        dependsOn("pipInstall")
        var cmd = "install"
        if (project.hasProperty("prod")) {
            cmd += " --prod"
        } else {
            cmd += " -G:all"
        }

        module = "pdm"
        command = cmd
    }

    clean {
        delete(virtualEnvDirectory, "coverage.xml", ".coverage")
    }

    create<PythonTask>("sphinx-autobuild") {
        module = "sphinx_autobuild"
        command = "--watch giskard docs docs/_build/html"
    }

    create<PythonTask>("lint") {
        dependsOn("install")
        module = "pdm"
        command = "lint"
    }

    create<PythonTask>("test") {
        dependsOn("install")
        module = "pdm"
        command = "run test-fast"
    }

    create<PythonTask>("test-all") {
        dependsOn("install")
        module = "pdm"
        command = "run test"
    }

    idea {
        module {
            excludeDirs.add(file(virtualEnvDirectory))
            excludeDirs.add(file("dist"))

            // "generated" directory should be marked as both source and generatedSource,
            // otherwise intellij doesn"t recognize it as a generated source 🤷‍
            testSources.from(file("tests"))
            inheritOutputDirs = false
            outputDir = file("dist")
            testOutputDir = file("dist")

        }
    }
    build {
        dependsOn("install", "test")
    }

    create<PythonTask>("start") {
        module = "giskard.cli"
        command = "worker start -s"
    }

    create<PythonTask>("package") {
        dependsOn("pipInstall")

        module = "pdm"
        command = "build"
    }
}

