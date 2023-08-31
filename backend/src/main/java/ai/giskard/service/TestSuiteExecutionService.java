package ai.giskard.service;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.ml.*;
import ai.giskard.exception.MLWorkerIllegalReplyException;
import ai.giskard.exception.MLWorkerNotConnectedException;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSErrorDTO;
import ai.giskard.ml.dto.MLWorkerWSTestSuiteDTO;
import ai.giskard.ml.dto.MLWorkerWSTestSuiteParamDTO;
import ai.giskard.repository.TestSuiteExecutionRepository;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
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
        if (GeneralSettingsService.IS_RUNNING_IN_DEMO_HF_SPACES) {
            workerID = MLWorkerID.INTERNAL;
        }
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            Map<String, FunctionInput> suiteInputsAndShared = Stream.concat(
                execution.getInputs().stream(),
                suite.getFunctionInputs().stream()
            ).collect(Collectors.toMap(FunctionInput::getName, Function.identity()));

            MLWorkerWSTestSuiteParamDTO param = MLWorkerWSTestSuiteParamDTO.builder()
                .globalArguments(execution.getInputs().stream().map(
                    input -> testArgumentService.buildTestArgumentWS(arguments, input.getName(),
                        input.getValue(), suite.getProject().getKey(), input.getParams(), sample)
                ).toList())
                .tests(suite.getTests().stream().map(
                    suiteTest -> testArgumentService.buildFixedTestArgumentWS(suiteInputsAndShared, suiteTest,
                        suite.getProject().getKey(), sample)
                ).toList())
                .build();

            Map<Long, SuiteTest> tests = suite.getTests().stream()
                .collect(Collectors.toMap(SuiteTest::getId, Function.identity()));

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                workerID,
                MLWorkerWSAction.RUN_TEST_SUITE,
                param
            );

            if (result instanceof MLWorkerWSTestSuiteDTO response) {
                execution.setResult(getResult(response));
                execution.setResults(response.getResults().stream()
                    .map(identifierSingleTestResult ->
                        new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution,
                            identifierSingleTestResult.getResult(), identifierSingleTestResult.getArguments()))
                    .toList());
                execution.setResults(response.getResults().stream()
                    .map(identifierSingleTestResult ->
                        new SuiteTestExecution(tests.get(identifierSingleTestResult.getId()), execution,
                            identifierSingleTestResult.getResult(), identifierSingleTestResult.getArguments()))
                    .toList());
                execution.setLogs(response.getLogs());
                execution.setCompletionDate(new Date());
                return;
            } else if (result instanceof MLWorkerWSErrorDTO error) {
                execution.setCompletionDate(new Date());
                throw new MLWorkerIllegalReplyException(error);
            }
            throw new MLWorkerIllegalReplyException("Cannot run test suite");
        }
        throw new MLWorkerNotConnectedException(workerID, log);
    }


    private static TestResult getResult(MLWorkerWSTestSuiteDTO testSuiteResultMessage) {
        if (Boolean.TRUE.equals(testSuiteResultMessage.getIsError())) {
            return TestResult.ERROR;
        } else if (Boolean.TRUE.equals(testSuiteResultMessage.getIsPass())) {
            return TestResult.PASSED;
        } else {
            return TestResult.FAILED;
        }
    }

}
