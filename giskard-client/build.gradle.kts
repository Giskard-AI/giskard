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
        minPythonVersion = "3.7.13"
        scope = VIRTUALENV
        installVirtualenv = true
        pip(listOf("poetry:1.2.2", "importlib-metadata:4.13.0"))
        environment = mapOf("PYTHONPATH" to file(protoGeneratedPath).absolutePath)
    }

    create<PythonTask>("install") {
        dependsOn("pipInstall")
        module = "poetry"
        command = "install"
    }

    clean {
        delete(protoGeneratedPath, virtualEnvDirectory, "coverage.xml", ".coverage")
    }

    create<PythonTask>("fixGeneratedFiles") {
        val script_path = file("scripts/fix_grpc_generated_imports.py")
        val fout = file(protoGeneratedPath)
        command = "$script_path $fout giskard.ml_worker.generated"
    }

    create<PythonTask>("generateProto") {
        dependsOn("install")
        environment("PATH", file(virtualEnvDirectory).resolve("bin"))

        val fout = file(protoGeneratedPath)
        val pdir = file("../common/proto")

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
            sourceDirs.add(file(protoGeneratedPath))
            generatedSourceDirs.add(file(protoGeneratedPath))

            testSourceDirs.add(file("tests"))
        }
    }
    build {
        dependsOn("install", "generateProto", "test")
    }

    create<PythonTask>("start") {
        module = "giskard.cli"
        command = "worker start -s"
    }
}

