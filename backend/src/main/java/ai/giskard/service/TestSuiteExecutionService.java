package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.ml.*;
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

import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
public class TestSuiteExecutionService {

    private final Logger log = LoggerFactory.getLogger(TestSuiteExecutionService.class);

    private final MLWorkerService mlWorkerService;
    private final TestArgumentService testArgumentService;
    private final TestSuiteExecutionRepository testSuiteExecutionRepository;
    private final GiskardMapper giskardMapper;

    public List<TestSuiteExecutionDTO> listAllExecution(long suiteId) {
        return giskardMapper.testSuiteExecutionToDTOs(testSuiteExecutionRepository.findAllBySuiteIdOrderByExecutionDateDesc(suiteId));
    }

    public void executeScheduledTestSuite(TestSuiteExecution execution,
                                          Map<String, String> suiteInputTypes,
                                          boolean sample) {
        TestSuite suite = execution.getSuite();

        Map<String, FunctionArgument> arguments = suiteInputTypes.entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> {
                FunctionArgument a = new FunctionArgument();
                a.setType(e.getValue());
                a.setOptional(false);
                return a;
            }));

        RunTestSuiteRequest.Builder builder = RunTestSuiteRequest.newBuilder();
        for (FunctionInput input : execution.getInputs()) {
            builder.addGlobalArguments(testArgumentService.buildTestArgument(arguments, input.getName(),
                input.getValue(), input.getParams(), sample));
        }

        Map<String, FunctionInput> suiteInputsAndShared = Stream.concat(
            execution.getInputs().stream(),
            suite.getFunctionInputs().stream()
        ).collect(Collectors.toMap(FunctionInput::getName, Function.identity()));

        for (SuiteTest suiteTest : suite.getTests()) {
            builder.addTests(testArgumentService.buildFixedTestArgument(suiteInputsAndShared, suiteTest,
                sample));
        }

        Map<Long, SuiteTest> tests = suite.getTests().stream()
            .collect(Collectors.toMap(SuiteTest::getId, Function.identity()));


        try (MLWorkerClient client = mlWorkerService.createClient(suite.getProject().isUsingInternalWorker())) {
            TestSuiteResultMessage testSuiteResultMessage = client.getBlockingStub().runTestSuite(builder.build());
            execution.setResult(getResult(testSuiteResultMessage));
            execution.setResults(testSuiteResultMessage.getResultsList().stream()
                .map(identifierSingleTestResult ->
                    new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution,
                        identifierSingleTestResult.getResult(), identifierSingleTestResult.getArgumentsList()))
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
