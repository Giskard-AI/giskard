import ru.vyarus.gradle.plugin.python.PythonExtension.Scope.USER
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
        pip(listOf("pdm:2.5.0", "urllib3:1.26.15"))
        environment = mapOf("PYTHONPATH" to file(protoGeneratedPath).absolutePath)
    }

    create<PythonTask>("install") {
        dependsOn("pipInstall")
        var cmd = "install -G:all"
        if (project.hasProperty("prod")) {
            cmd += " --prod"
        }

        module = "pdm"
        command = cmd
    }

    clean {
        delete(protoGeneratedPath, virtualEnvDirectory, "coverage.xml", ".coverage")
    }

    create<PythonTask>("fixGeneratedFiles") {
        val script_path = file("scripts/fix_grpc_generated_imports.py")
        val fout = file(protoGeneratedPath)
        command = "$script_path $fout giskard.ml_worker.generated"
    }

    create<PythonTask>("sphinx-autobuild") {
        module = "sphinx_autobuild"
        command = "docs docs/_build/html"
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

    create<PythonTask>("lint") {
        dependsOn("install")
        module = "pdm"
        command = "lint"
    }

    create<PythonTask>("test") {
        dependsOn("install")
        module = "pdm"
        command = "run test -m 'not slow'"
    }

    idea {
        module {
            excludeDirs.add(file(virtualEnvDirectory))
            excludeDirs.add(file("dist"))

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
        dependsOn("pipInstall")

        module = "pdm"
        command = "build"
    }
}

