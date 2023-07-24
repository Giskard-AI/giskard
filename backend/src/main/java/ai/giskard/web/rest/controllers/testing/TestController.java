package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.Project;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestArgumentService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.FunctionInputDTO;
import ai.giskard.web.dto.RunAdhocTestRequest;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO;
import ai.giskard.worker.RunAdHocTestRequest;
import ai.giskard.worker.TestResultMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;


@RestController
@RequestMapping("/api/v2/testing/tests")
@RequiredArgsConstructor
public class TestController {
    private final MLWorkerService mlWorkerService;
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
        try (MLWorkerClient client = mlWorkerService.createClient(usingInternalWorker)) {

            RunAdHocTestRequest.Builder builder = RunAdHocTestRequest.newBuilder()
                .setTestUuid(request.getTestUuid());

            for (FunctionInputDTO input : request.getInputs()) {

                builder.addArguments(testArgumentService
                    .buildTestArgument(arguments, input.getName(), input.getValue(), project.getKey(),
                        giskardMapper.fromDTO(input).getParams(), sample));
            }

            builder.setDebug(request.isDebug());

            TestResultMessage testResultMessage = client.getBlockingStub().runAdHocTest(builder.build());
            TestTemplateExecutionResultDTO res = new TestTemplateExecutionResultDTO(testFunction.getUuid());
            res.setResult(testResultMessage);
            if (testResultMessage.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
                res.setStatus(TestResult.FAILED);
            } else {
                res.setStatus(TestResult.PASSED);
            }
            return res;
        }
    }
}
