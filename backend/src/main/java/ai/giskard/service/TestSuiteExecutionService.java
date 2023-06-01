package ai.giskard.service;

import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.SuiteTestExecution;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import ai.giskard.worker.RunTestSuiteRequest;
import ai.giskard.worker.TestSuiteResultMessage;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class TestSuiteExecutionService {

    private final Logger log = LoggerFactory.getLogger(TestSuiteExecutionService.class);

    private final MLWorkerService mlWorkerService;
    private final TestArgumentService testArgumentService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;
    private final GiskardMapper giskardMapper;

    @Transactional(readOnly = true)
    public List<TestSuiteExecutionDTO> listAllExecution(long suiteId) {
        return giskardMapper.testSuiteExecutionToDTOs(testSuiteExecutionRepository.findAllBySuiteIdOrderByExecutionDateDesc(suiteId));
    }

    @Transactional(noRollbackFor = Exception.class)
    public void executeScheduledTestSuite(TestSuiteExecution execution, Map<String, String> suiteInputs) {
        try (MLWorkerClient client = mlWorkerService.createClient(execution.getSuite().getProject().isUsingInternalWorker())) {
            RunTestSuiteRequest.Builder builder = RunTestSuiteRequest.newBuilder()
                .addAllTestUuid(execution.getSuite().getTests().stream()
                    .map(test -> test.getTestFunction().getUuid().toString())
                    .collect(Collectors.toList()));

            for (Map.Entry<String, String> entry : execution.getInputs().entrySet()) {
                builder.addGlobalArguments(testArgumentService.buildTestArgument(suiteInputs, entry.getKey(), entry.getValue()));
            }

            for (SuiteTest suiteTest : execution.getSuite().getTests()) {
                builder.addFixedArguments(testArgumentService.buildFixedTestArgument(suiteTest));
            }

            TestSuiteResultMessage testSuiteResultMessage = client.getBlockingStub().runTestSuite(builder.build());

            Map<String, SuiteTest> tests = execution.getSuite().getTests().stream()
                .collect(Collectors.toMap(test -> test.getTestFunction().getUuid().toString(), Function.identity()));

            execution.setResult(testSuiteResultMessage.getIsPass() ? TestResult.PASSED : TestResult.FAILED);
            execution.setResults(testSuiteResultMessage.getResultsList().stream()
                .map(namedSingleTestResult ->
                    new SuiteTestExecution(tests.get(namedSingleTestResult.getTestUuid()), execution, namedSingleTestResult.getResult()))
                .collect(Collectors.toList()));
        } catch (Exception e) {
            log.error("Error while executing test suite {}", execution.getSuite().getName(), e);
            execution.setResult(TestResult.ERROR);
            execution.setMessage(e.getMessage());
            throw e;
        } finally {
            execution.setCompletionDate(new Date());
            testSuiteExecutionRepository.save(execution);
        }
    }

}
