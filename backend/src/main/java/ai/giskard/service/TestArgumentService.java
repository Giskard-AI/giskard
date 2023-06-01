package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.FuncArgument;
import ai.giskard.worker.SuiteTestArgument;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class TestArgumentService {

    public SuiteTestArgument buildFixedTestArgument(Map<String, String> globalArguments, SuiteTest test, String projectKey) {
        TestFunction testFunction = test.getTestFunction();
        SuiteTestArgument.Builder builder = SuiteTestArgument.newBuilder()
            .setTestUuid(testFunction.getUuid().toString())
            .setId(test.getId());

        Map<String, String> argumentTypes = testFunction.getArgs().stream()
            .collect(Collectors.toMap(FunctionArgument::getName, FunctionArgument::getType));


        for (FunctionInput input : test.getFunctionInputs()) {
            builder.addArguments(buildTestArgument(argumentTypes, input.getName(),
                input.isAlias() ? globalArguments.get(input.getValue()) : input.getValue(), projectKey, input.getParams()));
        }

        return builder.build();
    }

    public FuncArgument buildTestArgument(Map<String, String> testInputTypes,
                                          String inputName,
                                          String inputValue,
                                          String projectKey,
                                          List<FunctionInput> params) {
        return buildTestArgument(inputName, inputValue, projectKey, testInputTypes.get(inputName), params);
    }


    public FuncArgument buildTestArgument(String inputName, String inputValue, String projectKey,
                                          String inputType, List<FunctionInput> params) {
        FuncArgument.Builder argumentBuilder = FuncArgument.newBuilder()
            .setName(inputName);

        switch (inputType) {
            case "Dataset" -> argumentBuilder.setDataset(buildArtifactRef(projectKey, inputValue));
            case "BaseModel" -> argumentBuilder.setModel(buildArtifactRef(projectKey, inputValue));
            case "SlicingFunction" -> argumentBuilder.setSlicingFunction(buildArtifactRef(projectKey, inputValue));
            case "TransformationFunction" ->
                argumentBuilder.setTransformationFunction(buildArtifactRef(projectKey, inputValue));
            case "float" -> argumentBuilder.setFloat(Float.parseFloat(inputValue));
            case "int" -> argumentBuilder.setInt(Integer.parseInt(inputValue));
            case "str" -> argumentBuilder.setStr(inputValue);
            case "bool" -> argumentBuilder.setBool(Boolean.parseBoolean(inputValue));
            case "Kwargs" -> argumentBuilder.setKwargs(inputValue);
            default ->
                throw new IllegalArgumentException(String.format("Unknown test execution input type %s", inputType));
        }

        params.forEach(child -> argumentBuilder.addArgs(
            buildTestArgument(child.getName(), child.getValue(), projectKey, child.getType(), child.getParams())));

        return argumentBuilder.build();
    }

    private static ArtifactRef buildArtifactRef(String projectKey, String id) {
        return ArtifactRef.newBuilder()
            .setProjectKey(projectKey)
            .setId(id)
            .build();
    }

}
