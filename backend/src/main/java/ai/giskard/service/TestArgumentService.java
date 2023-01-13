package ai.giskard.service;

import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestInput;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;

@Service
@Transactional
@RequiredArgsConstructor
public class TestArgumentService {
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;

    public FixedTestArgument buildFixedTestArgument(SuiteTest test, TestFunction testFunction) {
        FixedTestArgument.Builder builder = FixedTestArgument.newBuilder()
            .setTestId(test.getTestId());

        Map<String, String> argumentTypes = Maps.transformValues(testFunction.getArgumentsMap(), TestFunctionArgument::getType);

        for (TestInput input : test.getTestInputs()) {
            builder.addArguments(buildTestArgument(argumentTypes, input.getName(), input.getValue()));
        }

        return builder.build();
    }

    public TestArgument buildTestArgument(Map<String, String> testInputTypes,
                                          String inputName,
                                          Object inputValue) {
        TestArgument.Builder argumentBuilder = TestArgument.newBuilder();
        argumentBuilder.setName(inputName);
        switch (testInputTypes.get(inputName)) {
            case "Dataset" -> {
                String projectKey = datasetRepository.getById(UUID.fromString((String) inputValue)).getProject().getKey();
                argumentBuilder.setDataset(
                    ArtifactRef.newBuilder()
                        .setProjectKey(projectKey)
                        .setId((String) inputValue)
                        .build()
                );
            }
            case "Model" -> {
                String projectKey = modelRepository.getById(UUID.fromString((String) inputValue)).getProject().getKey();
                argumentBuilder.setModel(
                    ArtifactRef.newBuilder()
                        .setProjectKey(projectKey)
                        .setId((String) inputValue)
                        .build()
                );
            }
            case "float" -> argumentBuilder.setFloat(Float.parseFloat(String.valueOf(inputValue)));
            case "string" -> argumentBuilder.setString((String) inputValue);
            default ->
                throw new IllegalArgumentException(String.format("Unknown test execution input type %s", testInputTypes.get(inputName)));
        }
        return argumentBuilder.build();
    }

}
