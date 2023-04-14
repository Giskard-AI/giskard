import ru.vyarus.gradle.plugin.python.PythonExtension.Scope.VIRTUALENV
import ru.vyarus.gradle.plugin.python.task.PythonTask

plugins {
    id("base")
    id("idea")
    id("org.sonarqube")
    id("ru.vyarus.use-python") version "3.0.0"
}

val protoGeneratedPath = "giskard/ml_worker/generated"
tasks {
    val virtualEnvDirectory = ".venv"
    python {
        envPath = virtualEnvDirectory
        minPythonVersion = "3.8"
        scope = VIRTUALENV
        installVirtualenv = true
        pip(listOf("pdm:2.5.0"))
        environment = mapOf("PYTHONPATH" to file(protoGeneratedPath).absolutePath)
    }

    create<PythonTask>("install") {
        dependsOn("pipInstall")
        module = "pdm"
        command = "install"
    }

    clean {
        delete(protoGeneratedPath, virtualEnvDirectory, "coverage.xml", ".coverage")
    }

    create<PythonTask>("proto") {
        module = "pdm"
        command = "proto"
    }

    create<PythonTask>("lint") {
        dependsOn("install")
        module = "pdm"
        command = "lint"
    }

    create<PythonTask>("test") {
        dependsOn("install")
        module = "pdm"
        // add "-n auto" to the pytest command to parallelize the execution
        command = "test"
    }

    idea {
        module {
            excludeDirs.add(file(virtualEnvDirectory))

            // "generated" directory should be marked as both source and generatedSource,
            // otherwise intellij doesn"t recognize it as a generated source 🤷‍
            sourceDirs.add(file(protoGeneratedPath))
            generatedSourceDirs.add(file(protoGeneratedPath))
            testSources.from(file("tests"))
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
        module = "pdm"
        command = "build"
    }
}

