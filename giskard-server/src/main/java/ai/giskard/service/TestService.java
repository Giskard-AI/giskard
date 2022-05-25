package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.ml.TestDTO;
import ai.giskard.web.dto.ml.TestExecutionResultDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.TestResultMessage;
import com.google.common.collect.Lists;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.ExecutionException;

@Service
@Transactional
@RequiredArgsConstructor
public class TestService {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(TestService.class);

    public static final int TEST_EXECUTION_CONCURRENCY = 5;

    private final MLWorkerService mlWorkerService;
    private final TestExecutionRepository testExecutionRepository;

    private final TestRepository testRepository;
    private final FileLocationService fileLocationService;

    public Optional<TestDTO> saveTest(TestDTO dto) {
        return Optional.of(testRepository.findById(dto.getId())).filter(Optional::isPresent).map(Optional::get).map(test -> {
            test.setName(dto.getName());
            test.setCode(dto.getCode());
            test.setLanguage(dto.getLanguage());
            test.setType(dto.getType());
            return testRepository.save(test);
        }).map(TestDTO::new);
    }

    @Transactional
    public TestExecutionResultDTO runTest(Long testId) {
        TestExecutionResultDTO res = new TestExecutionResultDTO(testId);
        Test test = testRepository.findById(testId).orElseThrow(() -> new EntityNotFoundException(Entity.TEST, testId));

        TestExecution testExecution = new TestExecution(test);
        testExecutionRepository.save(testExecution);
        res.setExecutionDate(testExecution.getExecutionDate());

        ProjectModel model = test.getTestSuite().getModel();
        Dataset trainDS = test.getTestSuite().getTrainDataset();
        Dataset testDS = test.getTestSuite().getTestDataset();
        Path modelPath = fileLocationService.resolvedModelPath(model.getProject().getKey(), model.getId());
        try (
            MLWorkerClient client = mlWorkerService.createClient();
            InputStream trainDSStream = Files.newInputStream(fileLocationService.resolvedDatasetPath(trainDS.getProject().getKey(), trainDS.getId()));
            InputStream testDSStream = Files.newInputStream(fileLocationService.resolvedDatasetPath(testDS.getProject().getKey(), testDS.getId()))) {

            TestResultMessage testResult = client.runTest(
                Files.newInputStream(modelPath),
                trainDSStream,
                testDSStream,
                test).get();

            res.setResult(testResult);
            if (testResult.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
                res.setStatus(TestResult.FAILED);
            } else {
                res.setStatus(TestResult.PASSED);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
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
        } catch (IOException e) {
            logger.warn("Failed to execute test due to IO error", e);
            res.setStatus(TestResult.ERROR);
            res.setMessage(ExceptionUtils.getMessage(e));
        }
        testExecution.setResult(res.getStatus());
        testExecutionRepository.save(testExecution);
        return res;
    }

    private void interpretTestExecutionError(TestSuite testSuite, Throwable e, TestExecutionResultDTO res) {
        if (e instanceof StatusRuntimeException statusRuntimeException) {
            String description = Objects.requireNonNull(statusRuntimeException.getStatus().getDescription());
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
        Lists.partition(testRepository.findAllByTestSuiteId(suiteId), TEST_EXECUTION_CONCURRENCY)
            .parallelStream().forEach(tests -> tests.forEach(test -> result.add(runTest(test.getId()))));
        return result;
    }
}
