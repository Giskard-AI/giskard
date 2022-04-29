package ai.giskard.service;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.web.dto.ml.TestDTO;
import ai.giskard.web.dto.ml.TestExecutionResultDTO;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.TestResultMessage;
import com.google.common.collect.Lists;
import com.google.common.util.concurrent.ListenableFuture;
import io.grpc.StatusRuntimeException;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ExecutionException;

@Service
@Transactional
public class TestService {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(TestService.class);

    public static final int TEST_EXECUTION_CONCURRENCY = 5;

    private final MLWorkerService mlWorkerService;
    private final TestExecutionRepository testExecutionRepository;

    private final TestRepository testRepository;

    public TestService(TestRepository testRepository, MLWorkerService mlWorkerService, TestExecutionRepository testExecutionRepository) {
        this.testRepository = testRepository;
        this.mlWorkerService = mlWorkerService;
        this.testExecutionRepository = testExecutionRepository;
    }


    public Optional<TestDTO> saveTest(TestDTO dto) {
        return Optional.of(testRepository.findById(dto.getId())).filter(Optional::isPresent).map(Optional::get).map(test -> {
            test.setName(dto.getName());
            test.setCode(dto.getCode());
            test.setLanguage(dto.getLanguage());
            test.setType(dto.getType());
            return testRepository.save(test);
        }).map(TestDTO::new);
    }

    public TestExecutionResultDTO runTest(Long testId) {
        TestExecutionResultDTO res = new TestExecutionResultDTO(testId);
        Test test = testRepository.findById(testId).orElseThrow(() -> new EntityNotFoundException(Entity.TEST, testId));

        TestExecution testExecution = new TestExecution(test);
        testExecutionRepository.save(testExecution);
        res.setExecutionDate(testExecution.getExecutionDate());

        MLWorkerClient client = null;
        try {
            client = mlWorkerService.createClient();
            ListenableFuture<TestResultMessage> runTestFuture = client.runTest(test.getTestSuite(), test);

            TestResultMessage testResult = runTestFuture.get();
            res.setResult(testResult);
            if (testResult.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
                res.setStatus(TestResult.FAILED);
            } else {
                res.setStatus(TestResult.PASSED);
            }
        } catch (InterruptedException e) {
            logger.error("Failed to create MLWorkerClient", e);
        } catch (ExecutionException e) {
            logger.warn("Test execution failed. Project: {}, Suite: {}, Test: {} ",
                test.getTestSuite().getProject().getId(),
                test.getTestSuite().getId(),
                test.getId(), e);
            res.setStatus(TestResult.ERROR);
            interpretTestExecutionError(test.getTestSuite(), e.getCause(), res);
            if (res.getMessage() == null) {
                res.setMessage(ExceptionUtils.getMessage(e));
            }
        } finally {
            if (client != null) {
                client.shutdown();
            }
        }
        testExecution.setResult(res.getStatus());
        testExecutionRepository.save(testExecution);
        return res;
    }

    private void applyTestExecutionResults(TestExecutionResultDTO res, TestResultMessage testResult) {
        res.setResult(testResult);
        if (testResult.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
            res.setStatus(TestResult.FAILED);
        } else {
            res.setStatus(TestResult.PASSED);
        }
    }

    private void interpretTestExecutionError(TestSuite testSuite, Throwable e, TestExecutionResultDTO res) {
        if (e instanceof StatusRuntimeException) {
            String description = Objects.requireNonNull(((StatusRuntimeException) e).getStatus().getDescription());
            if (description.contains("name 'train_df' is not defined") && testSuite.getTrainDataset() == null) {
                res.setMessage("Failed to execute test: Train dataset is not specified");
            } else if (description.contains("name 'test_df' is not defined") && testSuite.getTestDataset() == null) {
                res.setMessage("Failed to execute test: Test dataset is not specified");
            } else {
                res.setMessage(description);
            }
        }
    }

    public TestSuite deleteTest(Long testId) {
        Test test = testRepository.getById(testId);
        TestSuite testSuite = test.getTestSuite();
        testRepository.deleteById(testId);
        return testSuite;
    }

    public List<TestExecutionResultDTO> executeTestSuite(Long suiteId) {
        List<TestExecutionResultDTO> result = new ArrayList<>();
        Lists.partition(testRepository.findAllByTestSuiteId(suiteId), TEST_EXECUTION_CONCURRENCY).forEach(tests -> {
            tests.forEach(test -> {
                result.add(runTest(test.getId()));
            });
        });
        return result;
    }
}
