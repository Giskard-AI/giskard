package ai.giskard.utils;

import ai.giskard.domain.Project;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestSuite;
import org.springframework.util.FileSystemUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class ArtifactUtils {
    private ArtifactUtils() {}

    public static Set<TestFunction> getAllReferencedTestFunction(Project project) {
        return project.getTestSuites().stream().flatMap(ArtifactUtils::streamAllReferencedTestFunction)
            .collect(Collectors.toSet());
    }

    private static Stream<TestFunction> streamAllReferencedTestFunction(TestSuite project) {
        return Stream.concat(
            project.getTests().stream().map(SuiteTest::getTestFunction),
            project.getExecutions().stream().flatMap(testSuiteExecution -> testSuiteExecution.getResults().stream()
                .map(suiteTestExecution -> suiteTestExecution.getTest().getTestFunction()))
        );
    }

    public static Set<UUID> getAllReferencedTestInput(Project project, String inputType) {
        return project.getTestSuites().stream().flatMap(testSuite -> streamAllReferencedTestInput(testSuite, inputType))
            .collect(Collectors.toSet());
    }

    private static Stream<UUID> streamAllReferencedTestInput(TestSuite project, String inputType) {
        return project.getTests().stream()
            .flatMap(suiteTest -> suiteTest.getFunctionInputs().stream())
            .filter(functionInput -> !functionInput.isAlias() && inputType.equals(functionInput.getType()))
            .map(functionInput -> UUID.fromString(functionInput.getValue()));
    }

    public static void copyAllArtifactFolders(Path source, Path target, Set<UUID> uuids) throws IOException {
        if (!Files.exists(target)) {
            Files.createDirectories(target);
        }

        for (UUID uuid : uuids) {
            if (!Files.exists(target.resolve(uuid.toString()))) {
                FileSystemUtils.copyRecursively(source.resolve(uuid.toString()), target.resolve(uuid.toString()));
            }
        }
    }
}
