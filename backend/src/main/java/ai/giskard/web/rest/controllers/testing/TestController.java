package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.Project;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSFuncArgumentDTO;
import ai.giskard.ml.dto.MLWorkerWSRunAdHocTestDTO;
import ai.giskard.ml.dto.MLWorkerWSRunAdHocTestParamDTO;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestArgumentService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.web.dto.FunctionInputDTO;
import ai.giskard.web.dto.RunAdhocTestRequest;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO;
import ai.giskard.worker.RunAdHocTestRequest;
import ai.giskard.worker.TestResultMessage;
import com.fasterxml.jackson.core.JsonProcessingException;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;


@RestController
@RequestMapping("/api/v2/testing/tests")
@RequiredArgsConstructor
public class TestController {
    private final MLWorkerService mlWorkerService;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final ProjectRepository projectRepository;
    private final TestArgumentService testArgumentService;
    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;

    @PostMapping("/run-test")
    public TestTemplateExecutionResultDTO runAdHocTest(@RequestBody RunAdhocTestRequest request,
                                                       @RequestParam(required = false, defaultValue = "true") boolean sample) {
        TestFunction testFunction = testFunctionRepository.getWithArgsByUuid(UUID.fromString(request.getTestUuid()));
        Map<String, FunctionArgument> arguments = testFunction.getArgs().stream()
            .collect(Collectors.toMap(FunctionArgument::getName, Function.identity()));

        Project project = projectRepository.getMandatoryById(request.getProjectId());

        boolean usingInternalWorker = project.isUsingInternalWorker();
        MLWorkerID workerID = usingInternalWorker ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            MLWorkerWSRunAdHocTestParamDTO param = MLWorkerWSRunAdHocTestParamDTO.builder()
                .testUuid(request.getTestUuid())
                .arguments(request.getInputs().stream().map
                    (input -> testArgumentService
                        .buildTestArgumentWS(arguments, input.getName(), input.getValue(), project.getKey(),
                            giskardMapper.fromDTO(input).getParams(), sample)
                    ).collect(Collectors.toList())
                ).build();

            MLWorkerWSRunAdHocTestDTO response = null;
            MLWorkerWSBaseDTO result = null;
            try {
                result = mlWorkerWSCommService.performAction(
                    workerID,
                    MLWorkerWSAction.runAdHocTest,
                    param
                );
            } catch (JsonProcessingException e) {
                throw new RuntimeException(e);
            } catch (NullPointerException e) {
                throw new NullPointerException("Did not get a valid ML Worker RunAdHocTest reply");
            }
            if (result instanceof MLWorkerWSRunAdHocTestDTO) {
                response = (MLWorkerWSRunAdHocTestDTO) result;

                TestTemplateExecutionResultDTO res = new TestTemplateExecutionResultDTO(testFunction.getUuid());
                res.setResult(response);
                if (response.getResults().stream().anyMatch(r -> !r.getResult().getPassed())) {
                    res.setStatus(TestResult.FAILED);
                } else {
                    res.setStatus(TestResult.PASSED);
                }
                return res;
            }
        }
        throw new NullPointerException("Unable to get results of AdHoc test");
    }
}
