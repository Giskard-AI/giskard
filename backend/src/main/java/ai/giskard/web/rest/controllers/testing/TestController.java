package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.service.TestArgumentService;
import ai.giskard.service.TestService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.RunAdhocTestRequest;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO;
import ai.giskard.worker.*;
import com.google.common.collect.Maps;
import com.google.protobuf.Empty;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;


@RestController
@RequestMapping("/api/v2/testing/tests")
@RequiredArgsConstructor
public class TestController {
    private final TestService testService;
    private final MLWorkerService mlWorkerService;
    private final ProjectRepository projectRepository;
    private final TestArgumentService testArgumentService;

    @GetMapping("/test-catalog")
    @Transactional
    public TestCatalogDTO getTestTemplates(@RequestParam Long projectId) {
        return testService.listTestsFromRegistry(projectId);
    }

    @PostMapping("/run-test")
    @Transactional
    public TestTemplateExecutionResultDTO runAdHocTest(@RequestBody RunAdhocTestRequest request) {
        try (MLWorkerClient client = mlWorkerService.createClient(projectRepository.getById(request.getProjectId()).isUsingInternalWorker())) {
            TestRegistryResponse response = client.getBlockingStub().getTestRegistry(Empty.newBuilder().build());
            Map<String, TestFunction> registry = new HashMap<>();
            response.getTestsMap().values().forEach((TestFunction fn) -> registry.put(fn.getId(), fn));

            TestFunction test = registry.get(request.getTestId());
            Map<String, String> argumentTypes = Maps.transformValues(test.getArgumentsMap(), TestFunctionArgument::getType);

            RunAdHocTestRequest.Builder builder = RunAdHocTestRequest.newBuilder().setTestId(request.getTestId());

            for (Map.Entry<String, String> entry : request.getInputs().entrySet()) {
                builder.addArguments(testArgumentService.buildTestArgument(argumentTypes, entry.getKey(), entry.getValue()));
            }

            TestResultMessage testResultMessage = client.getBlockingStub().runAdHocTest(builder.build());
            TestTemplateExecutionResultDTO res = new TestTemplateExecutionResultDTO(test.getId());
            res.setResult(testResultMessage);
            if (testResultMessage.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
                res.setStatus(TestResult.FAILED);
            } else {
                res.setStatus(TestResult.PASSED);
            }
            return res;
        }

        //TestRegistryResponse response = mlWorkerService.createClient().getBlockingStub().getTestRegistry(Empty.newBuilder().build());

        //return JsonFormat.printer().print(response);
    }
}
