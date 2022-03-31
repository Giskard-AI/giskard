package ai.giskard.service;

import ai.giskard.domain.ml.TestResult;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.service.dto.ml.TestDTO;
import ai.giskard.service.dto.ml.TestExecutionResultDTO;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.worker.TestResultMessage;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class TestService {
    MLWorkerService mlWorkerService;
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(TestService.class);


    private final TestRepository testRepository;

    public TestService(TestRepository testRepository, MLWorkerService mlWorkerService) {
        this.testRepository = testRepository;
        this.mlWorkerService = mlWorkerService;
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
        MLWorkerClient client = null;
        try {
            client = mlWorkerService.createClient();
            TestResultMessage runTestResult = client.runTest(test.getTestSuite(), test);

            res.setStatus(TestResult.SUCCESS);
            res.setResult(runTestResult);
        } catch (InterruptedException e) {
            logger.error("Failed to crete MLWorkerClient", e);
        } catch (Exception e){
            res.setStatus(TestResult.ERROR);
            res.setMessage(e.getMessage());
        } finally {
            if (client != null) {
                client.shutdown();
            }
        }
        return res;
    }
}
