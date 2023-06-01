package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestInput;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.FixedTestArgument;
import ai.giskard.worker.TestArgument;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class TestArgumentService {
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;

    public FixedTestArgument buildFixedTestArgument(SuiteTest test) {
        TestFunction testFunction = test.getTestFunction();
        FixedTestArgument.Builder builder = FixedTestArgument.newBuilder()
            .setTestUuid(testFunction.getUuid().toString());

        Map<String, String> argumentTypes = testFunction.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgument::getName, TestFunctionArgument::getType));

        for (TestInput input : test.getTestInputs()) {
            builder.addArguments(buildTestArgument(argumentTypes, input.getName(), input.getValue()));
        }

        return builder.build();
    }

    public TestArgument buildTestArgument(Map<String, String> testInputTypes,
                                          String inputName,
                                          String inputValue) {
        TestArgument.Builder argumentBuilder = TestArgument.newBuilder()
            .setName(inputName);

        switch (testInputTypes.get(inputName)) {
            case "Dataset" -> {
                String projectKey = datasetRepository.getById(UUID.fromString(inputValue)).getProject().getKey();
                argumentBuilder.setDataset(
                    ArtifactRef.newBuilder()
                        .setProjectKey(projectKey)
                        .setId(inputValue)
                        .build()
                );
            }
            case "Model" -> {
                String projectKey = modelRepository.getById(UUID.fromString(inputValue)).getProject().getKey();
                argumentBuilder.setModel(
                    ArtifactRef.newBuilder()
                        .setProjectKey(projectKey)
                        .setId(inputValue)
                        .build()
                );
            }
            case "float" -> argumentBuilder.setFloat(Float.parseFloat(inputValue));
            case "string" -> argumentBuilder.setString(inputValue);
            default ->
                throw new IllegalArgumentException(String.format("Unknown test execution input type %s", testInputTypes.get(inputName)));
        }

        return argumentBuilder.build();
    }

}
