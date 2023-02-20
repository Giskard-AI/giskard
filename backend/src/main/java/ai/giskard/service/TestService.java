package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TestCatalogDTO;
import ai.giskard.web.dto.ml.TestDTO;
import ai.giskard.web.dto.ml.TestExecutionResultDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.RunTestRequest;
import ai.giskard.worker.TestRegistryResponse;
import ai.giskard.worker.TestResultMessage;
import com.google.common.collect.Lists;
import com.google.protobuf.Empty;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@Transactional
@RequiredArgsConstructor
public class TestService {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(TestService.class);

    public static final int TEST_EXECUTION_CONCURRENCY = 5;

    private final MLWorkerService mlWorkerService;
    private final TestExecutionRepository testExecutionRepository;

    private final TestRepository testRepository;
    private final ProjectRepository projectRepository;

    private final GRPCMapper grpcMapper;

    public Optional<TestDTO> saveTest(TestDTO dto) {
        return Optional.of(testRepository.findById(dto.getId())).filter(Optional::isPresent).map(Optional::get).map(test -> {
            test.setName(dto.getName());
            test.setCode(dto.getCode());
            test.setLanguage(dto.getLanguage());
            test.setType(dto.getType());
            return testRepository.save(test);
        }).map(TestDTO::new);
    }

    @Transactional(noRollbackFor = StatusRuntimeException.class)
    public TestExecutionResultDTO runTest(Long testId) {
        return runTest(testId, true);
    }

    @Transactional()
    public TestExecutionResultDTO runTestNoError(Long testId) {
        return runTest(testId, false);
    }

    private TestExecutionResultDTO runTest(Long testId, boolean throwExceptionOnError) {
        TestExecutionResultDTO res = new TestExecutionResultDTO(testId);
        Test test = testRepository.findById(testId).orElseThrow(() -> new EntityNotFoundException(Entity.TEST, testId));
        res.setTestName(test.getName());
        logger.info("Running test {}({}) for suite {}, project {}",
            test.getName(), test.getId(), test.getTestSuite().getId(), test.getTestSuite().getProject().getKey());

        TestExecution testExecution = new TestExecution(test);
        testExecutionRepository.save(testExecution);
        res.setExecutionDate(testExecution.getExecutionDate().toInstant());

        ProjectModel model = test.getTestSuite().getModel();
        Dataset referenceDS = test.getTestSuite().getReferenceDataset();
        Dataset actualDS = test.getTestSuite().getActualDataset();
        try (MLWorkerClient client = mlWorkerService.createClient(test.getTestSuite().getProject().isUsingInternalWorker())) {
            TestResultMessage testResult;

            RunTestRequest.Builder requestBuilder = RunTestRequest.newBuilder()
                .setCode(test.getCode())
                .setModel(grpcMapper.createRef(model));
            if (referenceDS != null) {
                requestBuilder.setReferenceDs(grpcMapper.createRef(referenceDS));
            }
            if (actualDS != null) {
                requestBuilder.setActualDs(grpcMapper.createRef(actualDS));
            }
            RunTestRequest request = requestBuilder.build();
            logger.debug("Sending requiest to ML Worker: {}", request);
            try {
                testResult = client.getBlockingStub().runTest(request);
                res.setResult(testResult);
                if (testResult.getResultsList().stream().anyMatch(r -> !r.getResult().getPassed())) {
                    res.setStatus(TestResult.FAILED);
                } else {
                    res.setStatus(TestResult.PASSED);
                }
            } catch (StatusRuntimeException e) {
                if (throwExceptionOnError) {
                    testExecution.setResult(TestResult.ERROR);
                    testExecutionRepository.save(testExecution);
                    throw e;
                } else {
                    res.setStatus(TestResult.ERROR);
                    res.setMessage(e.getCause().getMessage());
                }
            }
        }
        testExecution.setResult(res.getStatus());
        testExecutionRepository.save(testExecution);
        return res;
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
            .parallelStream().forEach(tests -> tests.forEach(test -> {
                Long testId = test.getId();
                try {
                    TestExecutionResultDTO res = runTestNoError(testId);
                    result.add(res);
                } catch (Exception e) {
                    logger.error("Failed to run test {} in suite {}", testId, test.getTestSuite().getId(), e);
                }
            }));
        return result;
    }

    public TestCatalogDTO listTestsFromRegistry(Long projectId) {
        try (MLWorkerClient client = mlWorkerService.createClient(projectRepository.getById(projectId).isUsingInternalWorker())) {
            TestRegistryResponse response = client.getBlockingStub().getTestRegistry(Empty.newBuilder().build());
            return convertGRPCObject(response, TestCatalogDTO.class);
        }
    }
}
