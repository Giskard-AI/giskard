package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.ml.dto.MLWorkerWSArtifactRefDTO;
import ai.giskard.ml.dto.MLWorkerWSFuncArgumentDTO;
import ai.giskard.ml.dto.MLWorkerWSSuiteTestArgumentDTO;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TestArgumentService {

    public MLWorkerWSSuiteTestArgumentDTO buildFixedTestArgumentWS(Map<String, FunctionInput> globalArguments, SuiteTest test, String projectKey,
                                                                   boolean sample) {
        TestFunction testFunction = test.getTestFunction();
        MLWorkerWSSuiteTestArgumentDTO argument = new MLWorkerWSSuiteTestArgumentDTO();
        argument.setTestUuid(testFunction.getUuid().toString());
        argument.setId(test.getId());

        Map<String, FunctionArgument> arguments = testFunction.getArgs().stream()
            .collect(Collectors.toMap(FunctionArgument::getName, Function.identity()));

        List<MLWorkerWSFuncArgumentDTO> args = new ArrayList<>(test.getFunctionInputs().size());
        for (FunctionInput input : test.getFunctionInputs()) {
            if (input.isAlias()) {
                FunctionInput shared = globalArguments.get(input.getValue());
                args.add(buildTestArgumentWS(arguments, shared.getName(), shared.getValue(), projectKey, shared.getParams(), sample));
            } else {
                args.add(buildTestArgumentWS(arguments, input.getName(), input.getValue(), projectKey, input.getParams(), sample));
            }
        }
        argument.setArguments(args);

        return argument;
    }

    public MLWorkerWSFuncArgumentDTO buildTestArgumentWS(Map<String, FunctionArgument> arguments,
                                          String inputName,
                                          String inputValue,
                                          String projectKey,
                                          List<FunctionInput> params,
                                          boolean sample) {
        FunctionArgument argument = arguments.get(inputName);
        if (Strings.isBlank(inputValue) && !argument.isOptional()) {
            throw new IllegalArgumentException("The required argument '" + inputName + "' was not provided");
        }

        String value = Strings.isBlank(inputValue) ? argument.getDefaultValue() : inputValue;

        return buildTestArgumentWS(inputName, value, projectKey, argument.getType(), params, sample);
    }


    public MLWorkerWSFuncArgumentDTO buildTestArgumentWS(String inputName, String inputValue, String projectKey,
                                                         String inputType, List<FunctionInput> params, boolean sample) {
        MLWorkerWSFuncArgumentDTO.MLWorkerWSFuncArgumentDTOBuilder argument = MLWorkerWSFuncArgumentDTO.builder()
            .name(inputName);

        if (inputValue.equals("None")) {
            argument.none(true);
            return argument.build();
        }

        argument.none(false);

        MLWorkerWSArtifactRefDTO ref = MLWorkerWSArtifactRefDTO.builder()
            .projectKey(projectKey)
            .id(inputValue)
            .sample(sample)
            .build();
        switch (inputType) {
            case "Dataset" -> argument.dataset(ref);
            case "BaseModel" -> argument.model(ref);
            case "SlicingFunction" -> argument.slicingFunction(ref);
            case "TransformationFunction" ->
                argument.transformationFunction(ref);
            case "float" -> argument.floatValue(Float.parseFloat(inputValue));
            case "int" -> argument.intValue(Integer.parseInt(inputValue));
            case "str" -> argument.strValue(inputValue);
            case "bool" -> argument.boolValue(Boolean.parseBoolean(inputValue));
            case "Kwargs" -> argument.kwargs(inputValue);
            default ->
                throw new IllegalArgumentException(String.format("Unknown test execution input type %s", inputType));
        }

        if (params != null) {
            argument.args(params.stream().map(child ->
                    buildTestArgumentWS(
                        child.getName(), child.getValue(), projectKey, child.getType(), child.getParams(), sample
                    )
                ).toList()
            );
        }

        return argument.build();
    }
}
