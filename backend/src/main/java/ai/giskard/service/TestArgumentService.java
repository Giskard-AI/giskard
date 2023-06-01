package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.TestInput;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.SuiteTestArgument;
import ai.giskard.worker.TestArgument;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class TestArgumentService {

    public SuiteTestArgument buildFixedTestArgument(SuiteTest test, String projectKey) {
        TestFunction testFunction = test.getTestFunction();
        SuiteTestArgument.Builder builder = SuiteTestArgument.newBuilder()
            .setTestUuid(testFunction.getUuid().toString())
            .setId(test.getId());

        Map<String, String> argumentTypes = testFunction.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgument::getName, TestFunctionArgument::getType));

        for (TestInput input : test.getTestInputs()) {
            builder.addArguments(buildTestArgument(argumentTypes, input.getName(), input.getValue(), projectKey));
        }

        return builder.build();
    }

    public TestArgument buildTestArgument(Map<String, String> testInputTypes,
                                          String inputName,
                                          String inputValue,
                                          String projectKey) {
        return buildTestArgument(inputName, inputValue, projectKey, testInputTypes.get(inputName));
    }

    public TestArgument buildTestArgument(String inputName, String inputValue, String projectKey, String inputType) {
        TestArgument.Builder argumentBuilder = TestArgument.newBuilder()
            .setName(inputName);

        switch (inputType) {
            case "Dataset" -> argumentBuilder.setDataset(buildArtifactRef(projectKey, inputValue));
            case "Model" -> argumentBuilder.setModel(buildArtifactRef(projectKey, inputValue));
            case "float" -> argumentBuilder.setFloat(Float.parseFloat(inputValue));
            case "int" -> argumentBuilder.setInt(Integer.parseInt(inputValue));
            case "str" -> argumentBuilder.setStr(inputValue);
            case "bool" -> argumentBuilder.setBool(Boolean.parseBoolean(inputValue));
            default ->
                throw new IllegalArgumentException(String.format("Unknown test execution input type %s", inputType));
        }

        return argumentBuilder.build();
    }

    private static ArtifactRef buildArtifactRef(String projectKey, String id) {
        return ArtifactRef.newBuilder()
            .setProjectKey(projectKey)
            .setId(id)
            .build();
    }

}
