package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.ml.*;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import ai.giskard.worker.TestSuiteResultMessage;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
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
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
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

        MLWorkerID workerID = suite.getProject().isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        MLWorkerWSTestSuiteDTO response = null;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {

            MLWorkerWSTestSuiteParamDTO param = new MLWorkerWSTestSuiteParamDTO();
            List<MLWorkerWSFuncArgumentDTO> globalArguments = new ArrayList<>(execution.getInputs().size());
            for (FunctionInput input : execution.getInputs()) {
                globalArguments.add(testArgumentService.buildTestArgumentWS(arguments, input.getName(),
                    input.getValue(), suite.getProject().getKey(), input.getParams(), sample));
            }
            param.setGlobalArguments(globalArguments);

            Map<String, FunctionInput> suiteInputsAndShared = Stream.concat(
                execution.getInputs().stream(),
                suite.getFunctionInputs().stream()
            ).collect(Collectors.toMap(FunctionInput::getName, Function.identity()));

            List<MLWorkerWSSuiteTestArgumentDTO> suiteTests = new ArrayList<>(suite.getTests().size());
            for (SuiteTest suiteTest : suite.getTests()) {
                suiteTests.add(testArgumentService.buildFixedTestArgumentWS(suiteInputsAndShared, suiteTest,
                    suite.getProject().getKey(), sample));
            }
            param.setTests(suiteTests);

            Map<Long, SuiteTest> tests = suite.getTests().stream()
                .collect(Collectors.toMap(SuiteTest::getId, Function.identity()));

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                workerID,
                MLWorkerWSAction.runTestSuite,
                param
            );

            if (result != null && result instanceof MLWorkerWSTestSuiteDTO) {
                response = (MLWorkerWSTestSuiteDTO) result;
                execution.setResult(getResult(response));
                execution.setResults(response.getResults().stream()
                    .map(identifierSingleTestResult ->
                        new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution,
                            identifierSingleTestResult.getResult()))
                    .collect(Collectors.toList()));
            }

            execution.setResults(response.getResults().stream()
                .map(identifierSingleTestResult ->
                    new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution,
                        identifierSingleTestResult.getResult()))
                .collect(Collectors.toList()));
            execution.setLogs(response.getLogs());
        }
        throw new NullPointerException("Error while executing test suite");
    }


    private static TestResult getResult(MLWorkerWSTestSuiteDTO testSuiteResultMessage) {
        if (testSuiteResultMessage.getIsError()) {
            return TestResult.ERROR;
        } else if (testSuiteResultMessage.getIsPass()) {
            return TestResult.PASSED;
        } else {
            return TestResult.FAILED;
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
