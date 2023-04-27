package ai.giskard.service;

import ai.giskard.domain.ml.*;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import ai.giskard.worker.RunTestSuiteRequest;
import ai.giskard.worker.TestSuiteResultMessage;
import lombok.RequiredArgsConstructor;
import org.apache.logging.log4j.util.Strings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TestSuiteExecutionService {

    private final Logger log = LoggerFactory.getLogger(TestSuiteExecutionService.class);

    private final MLWorkerService mlWorkerService;
    private final TestArgumentService testArgumentService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;
    private final TestSuiteRepository testSuiteRepository;
    private final GiskardMapper giskardMapper;

    public List<TestSuiteExecutionDTO> listAllExecution(long suiteId) {
        return giskardMapper.testSuiteExecutionToDTOs(testSuiteExecutionRepository.findAllBySuiteIdOrderByExecutionDateDesc(suiteId));
    }

    public void executeScheduledTestSuite(TestSuiteExecution execution, Map<String, String> suiteInputs) {
        TestSuite suite = execution.getSuite();

        RunTestSuiteRequest.Builder builder = RunTestSuiteRequest.newBuilder();
        for (Map.Entry<String, String> entry : execution.getInputs().entrySet()) {
            builder.addGlobalArguments(testArgumentService.buildTestArgument(suiteInputs, entry.getKey(),
                entry.getValue(), suite.getProject().getKey(), Collections.emptyList()));
        }

        Map<String, String> suiteInputsAndShared = new HashMap<>(execution.getInputs());
        suite.getFunctionInputs().stream()
            .filter(i -> Strings.isNotBlank(i.getValue()))
            .forEach(i -> suiteInputsAndShared.put(i.getName(), i.getValue()));

        for (SuiteTest suiteTest : suite.getTests()) {
            builder.addTests(testArgumentService.buildFixedTestArgument(suiteInputsAndShared, suiteTest, suite.getProject().getKey()));
        }
        Map<Long, SuiteTest> tests = suite.getTests().stream()
            .collect(Collectors.toMap(SuiteTest::getId, Function.identity()));


        try (MLWorkerClient client = mlWorkerService.createClient(suite.getProject().isUsingInternalWorker())) {
            TestSuiteResultMessage testSuiteResultMessage = client.getBlockingStub().runTestSuite(builder.build());

            execution.setResult(getResult(testSuiteResultMessage));
            execution.setResults(testSuiteResultMessage.getResultsList().stream()
                .map(identifierSingleTestResult ->
                    new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution, identifierSingleTestResult.getResult()))
                .collect(Collectors.toList()));
            execution.setLogs(testSuiteResultMessage.getLogs());
        } catch (Exception e) {
            log.error("Error while executing test suite {}", suite.getName(), e);
            execution.setResult(TestResult.ERROR);
            execution.setLogs(e.getMessage());
            throw e;
        } finally {
            execution.setCompletionDate(new Date());
        }
    }

    private static TestResult getResult(TestSuiteResultMessage testSuiteResultMessage) {
        if (testSuiteResultMessage.getIsError()) {
            return TestResult.ERROR;
        } else if (testSuiteResultMessage.getIsPass()) {
            return TestResult.PASSED;
        } else {
            return TestResult.FAILED;
        }
    }

}
