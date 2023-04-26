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
import ai.giskard.web.dto.RunAdhocTestRequest;
import ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO;
import ai.giskard.worker.RunAdHocTestRequest;
import ai.giskard.worker.TestResultMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Collections;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;


@RestController
@RequestMapping("/api/v2/testing/tests")
@RequiredArgsConstructor
public class TestController {
    private final MLWorkerService mlWorkerService;
    private final ProjectRepository projectRepository;
    private final TestArgumentService testArgumentService;

    private final TestFunctionRepository testFunctionRepository;

    @PostMapping("/run-test")
    public TestTemplateExecutionResultDTO runAdHocTest(@RequestBody RunAdhocTestRequest request) {
        TestFunction testFunction = testFunctionRepository.getWithArgsByUuid(UUID.fromString(request.getTestUuid()));
        Map<String, String> argumentTypes = testFunction.getArgs().stream()
            .collect(Collectors.toMap(FunctionArgument::getName, FunctionArgument::getType));

        Project project = projectRepository.getMandatoryById(request.getProjectId());

        boolean usingInternalWorker = project.isUsingInternalWorker();
        try (MLWorkerClient client = mlWorkerService.createClient(usingInternalWorker)) {

            RunAdHocTestRequest.Builder builder = RunAdHocTestRequest.newBuilder()
                .setTestUuid(request.getTestUuid());

            for (Map.Entry<String, String> entry : request.getInputs().entrySet()) {
                builder.addArguments(testArgumentService
                    .buildTestArgument(argumentTypes, entry.getKey(), entry.getValue(), project.getKey(), Collections.emptyList()));
            }

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
