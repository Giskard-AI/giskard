package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.FuncArgument;
import ai.giskard.worker.SuiteTestArgument;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TestArgumentService {

    public SuiteTestArgument buildFixedTestArgument(Map<String, FunctionInput> globalArguments, SuiteTest test,
                                                    boolean sample) {
        TestFunction testFunction = test.getTestFunction();
        SuiteTestArgument.Builder builder = SuiteTestArgument.newBuilder()
                .setTestUuid(testFunction.getUuid().toString())
                .setId(test.getId());

        Map<String, FunctionArgument> arguments = testFunction.getArgs().stream()
                .collect(Collectors.toMap(FunctionArgument::getName, Function.identity()));


        for (FunctionInput input : test.getFunctionInputs()) {
            if (input.isAlias()) {
                FunctionInput shared = globalArguments.get(input.getValue());
                builder.addArguments(buildTestArgument(arguments, shared.getName(), shared.getValue(), shared.getParams(), sample));
            } else {
                builder.addArguments(buildTestArgument(arguments, input.getName(), input.getValue(), input.getParams(), sample));
            }

        }

        return builder.build();
    }

    public FuncArgument buildTestArgument(Map<String, FunctionArgument> arguments,
                                          String inputName,
                                          String inputValue,
                                          List<FunctionInput> params,
                                          boolean sample) {
        FunctionArgument argument = arguments.get(inputName);
        if (Strings.isBlank(inputValue) && !argument.isOptional()) {
            throw new IllegalArgumentException("The required argument '" + inputName + "' was not provided");
        }

        String value = Strings.isBlank(inputValue) ? argument.getDefaultValue() : inputValue;

        return buildTestArgument(inputName, value, argument.getType(), params, sample);
    }


    public FuncArgument buildTestArgument(String inputName, String inputValue,
                                          String inputType, List<FunctionInput> params, boolean sample) {
        FuncArgument.Builder argumentBuilder = FuncArgument.newBuilder()
                .setName(inputName);

        if (inputValue.equals("None")) {
            argumentBuilder.setNone(true);
            return argumentBuilder.build();
        }

        argumentBuilder.setNone(false);
        if (inputType == null) {
            throw new IllegalArgumentException("Empty input type for input `%s`".formatted(inputName));
        }

        switch (inputType) {
            case "Dataset" -> argumentBuilder.setDataset(buildArtifactRef(inputValue).setSample(sample));
            case "BaseModel" -> argumentBuilder.setModel(buildArtifactRef(inputValue));
            case "SlicingFunction" -> argumentBuilder.setSlicingFunction(buildArtifactRef(inputValue));
            case "TransformationFunction" -> argumentBuilder.setTransformationFunction(buildArtifactRef(inputValue));
            case "float" -> argumentBuilder.setFloat(Float.parseFloat(inputValue));
            case "int" -> argumentBuilder.setInt(Integer.parseInt(inputValue));
            case "str" -> argumentBuilder.setStr(inputValue);
            case "bool" -> argumentBuilder.setBool(Boolean.parseBoolean(inputValue));
            case "Kwargs" -> argumentBuilder.setKwargs(inputValue);
            default ->
                    throw new IllegalArgumentException(String.format("Unknown test execution input type %s", inputType));
        }

        if (params != null) {
            params.forEach(child -> argumentBuilder.addArgs(
                    buildTestArgument(child.getName(), child.getValue(), child.getType(), child.getParams(), sample)));
        }

        return argumentBuilder.build();
    }

    private static ArtifactRef.Builder buildArtifactRef(String id) {
        return ArtifactRef.newBuilder()
                .setId(id);
    }

}
