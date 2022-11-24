import ru.vyarus.gradle.plugin.python.PythonExtension.Scope.VIRTUALENV
import ru.vyarus.gradle.plugin.python.task.PythonTask

plugins {
    id("base")
    id("idea")
    id("org.sonarqube")
    id("ru.vyarus.use-python") version "3.0.0"
}

sonarqube {
    properties {
        property("sonar.python.version", "3")
        property("sonar.sources", "ml_worker")
        property("sonar.tests", "test")
        property("sonar.language", "python")
        property("sonar.sourceEncoding", "UTF-8")
        property("sonar.dynamicAnalysis", "reuseReports")
        property("sonar.core.codeCoveragePlugin", "cobertura")
        property("sonar.python.coverage.reportPaths", "coverage.xml")
    }
}
tasks {
    val virtualEnvDirectory = ".venv"
    python {
        envPath = virtualEnvDirectory
        minPythonVersion = "3.7"
        scope = VIRTUALENV
        installVirtualenv = true
        pip(listOf("poetry:1.2.2"))
        environment = mapOf("PYTHONPATH" to file("generated").absolutePath)
    }

    create<PythonTask>("install") {
        dependsOn("pipInstall")
        module = "poetry"
        command = "install"
    }

    clean {
        delete("generated", virtualEnvDirectory, "coverage.xml", ".coverage")
    }

    create<PythonTask>("fixGeneratedFiles") {
        val script_path = file("scripts/fix_grpc_generated_imports.py")
        val fout = file("generated")
        command = "$script_path $fout giskard.ml_worker.generated"
    }

    create<PythonTask>("generateProto") {
        dependsOn("install")
        environment("PATH", file(virtualEnvDirectory).resolve("bin"))

        val fout = file("generated")
        val pdir = file("../giskard-common/proto")

        doFirst {
            mkdir(fout)
        }

        finalizedBy("fixGeneratedFiles")

        module = "grpc_tools.protoc"

        command =
            "-I$pdir --python_out=$fout --grpc_python_out=$fout --mypy_out=$fout --mypy_grpc_out=$fout $pdir/ml-worker.proto"

    }

    create<PythonTask>("test") {
        module = "pytest"
        command = "-c ${file("pyproject.toml")} --cov=giskard tests --cov-report=xml"
    }


    idea {
        module {
            excludeDirs.add(file(virtualEnvDirectory))

            // "generated" directory should be marked as both source and generatedSource,
            // otherwise intellij doesn"t recognize it as a generated source 🤷‍
            sourceDirs.add(file("generated"))
            generatedSourceDirs.add(file("generated"))

            testSourceDirs.add(file("test"))
        }
    }
    build {
        dependsOn("install", "generateProto", "test")
    }
}

