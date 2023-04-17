package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.Project;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestArgumentService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.RunAdhocTestRequest;
import ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.RunAdHocTestRequest;
import ai.giskard.worker.TestResultMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

import static ai.giskard.web.rest.errors.Entity.TEST_FUNCTION;


@RestController
@RequestMapping("/api/v2/testing/tests")
@RequiredArgsConstructor
public class TestController {
    private final MLWorkerService mlWorkerService;
    private final ProjectRepository projectRepository;
    private final TestArgumentService testArgumentService;

    private final TestFunctionRepository testFunctionRepository;

    @PostMapping("/run-test")
    @Transactional(readOnly = true)
    public TestTemplateExecutionResultDTO runAdHocTest(@RequestBody RunAdhocTestRequest request) {
        TestFunction testFunction = testFunctionRepository.findById(UUID.fromString(request.getTestUuid()))
            .orElseThrow(() -> new EntityNotFoundException(TEST_FUNCTION, request.getTestUuid()));

        Project project = projectRepository.getById(request.getProjectId());

        try (MLWorkerClient client = mlWorkerService.createClient(projectRepository.getById(request.getProjectId()).isUsingInternalWorker())) {
            Map<String, String> argumentTypes = testFunction.getArgs().stream()
                .collect(Collectors.toMap(TestFunctionArgument::getName, TestFunctionArgument::getType));

            RunAdHocTestRequest.Builder builder = RunAdHocTestRequest.newBuilder()
                .setTestUuid(request.getTestUuid());

            for (Map.Entry<String, String> entry : request.getInputs().entrySet()) {
                builder.addArguments(testArgumentService.buildTestArgument(argumentTypes, entry.getKey(), entry.getValue(), project.getKey()));
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
