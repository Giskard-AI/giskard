package ai.giskard.service;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.service.dto.ml.TestDTO;
import ai.giskard.service.dto.ml.TestExecutionResultDTO;
import ai.giskard.service.ml.MLWorkerService;
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

@Service
@Transactional
public class TestService {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(TestService.class);

    public static final int TEST_EXECUTION_CONCURRENCY = 5;

    private final MLWorkerService mlWorkerService;
    private final TestExecutionRepository testExecutionRepository;

    private final TestRepository testRepository;

    public TestService(TestRepository testRepository, MLWorkerService mlWorkerService,
                       TestExecutionRepository testExecutionRepository) {
        this.testRepository = testRepository;
        this.mlWorkerService = mlWorkerService;
        this.testExecutionRepository = testExecutionRepository;
    }


    public Optional<TestDTO> saveTest(TestDTO dto) {
        return Optional
            .of(testRepository.findById(dto.getId()))
            .filter(Optional::isPresent)
            .map(Optional::get)
            .map(test -> {
                test.setName(dto.getName());
                test.setCode(dto.getCode());
                test.setLanguage(dto.getLanguage());
                test.setType(dto.getType());
                return testRepository.save(test);
            })
            .map(TestDTO::new);
    }

    public TestExecutionResultDTO runTest(Long testId) {
        TestExecutionResultDTO res = new TestExecutionResultDTO();
        Test test = testRepository.findById(testId).orElseThrow(() -> new EntityNotFoundException(EntityNotFoundException.Entity.TEST, testId));

        TestExecution testExecution = new TestExecution(test);
        testExecutionRepository.save(testExecution);

        MLWorkerClient client = null;
        try {
            client = mlWorkerService.createClient();
            ListenableFuture<TestResultMessage> runTestFuture = client.runTest(test.getTestSuite(), test);

            res.setResult(runTestFuture.get());
            res.setStatus(TestResult.SUCCESS);
        } catch (InterruptedException e) {
            logger.error("Failed to crete MLWorkerClient", e);
        } catch (StatusRuntimeException e) {
            interpretTestExecutionError(test.getTestSuite(), e, res);
        } catch (Exception e) {
            res.setStatus(TestResult.ERROR);
            res.setMessage(ExceptionUtils.getMessage(e));
        } finally {
            if (client != null) {
                client.shutdown();
            }
        }
        testExecution.setResult(res.getStatus());
        testExecutionRepository.save(testExecution);
        return res;
    }

    private void interpretTestExecutionError(TestSuite testSuite, StatusRuntimeException e, TestExecutionResultDTO res) {
        res.setStatus(TestResult.ERROR);
        switch (Objects.requireNonNull(e.getStatus().getDescription())) {
            case "Exception calling application: name 'train_df' is not defined":
                if (testSuite.getTrainDataset() == null) {
                    res.setMessage("Failed to execute test: Train dataset is not specified");
                }
            case "Exception calling application: name 'test_df' is not defined":
                if (testSuite.getTestDataset() == null) {
                    res.setMessage("Failed to execute test: Test dataset is not specified");
                }
            default:
                throw e;
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
