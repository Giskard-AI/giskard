package ai.giskard.web.rest.testing;

import ai.giskard.domain.ml.testing.Test;
import ai.giskard.domain.ml.testing.TestExecution;
import ai.giskard.repository.ml.TestExecutionRepository;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.dto.ml.TestDTO;
import ai.giskard.service.dto.ml.TestEditorConfigDTO;
import ai.giskard.service.dto.ml.TestExecutionResultDTO;
import ai.giskard.service.dto.ml.TestSuiteDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static ai.giskard.web.rest.errors.EntityNotFoundException.Entity.TEST_SUITE;

@RestController
@RequestMapping("/api/v2/testing/tests")
public class TestController {
    private final TestRepository testRepository;
    private final TestService testService;
    private final TestSuiteRepository testSuiteRepository;
    private final TestExecutionRepository testExecutionRepository;

    public TestController(TestService testService, TestSuiteRepository testSuiteRepository,
                          TestRepository testRepository, TestExecutionRepository testExecutionRepository) {
        this.testService = testService;
        this.testSuiteRepository = testSuiteRepository;
        this.testRepository = testRepository;
        this.testExecutionRepository = testExecutionRepository;
    }

    @GetMapping("")
    public List<TestDTO> getTests(
        @RequestParam Long suiteId
    ) {
        return testRepository.findAllByTestSuiteId(suiteId).stream().map(test -> {
            TestDTO res = new TestDTO(test);
            Optional<TestExecution> exec = testExecutionRepository.findFirstByTestIdOrderByExecutionDateDesc(test.getId());
            exec.ifPresent(testExecution -> {
                res.setStatus(testExecution.getResult());
                res.setLastExecutionDate(testExecution.getExecutionDate());
            });
            return res;
        }).collect(Collectors.toList());
    }

    @GetMapping("/{testId}")
    public TestDTO getTest(
        @PathVariable() Long testId
    ) {
        Optional<Test> test = testRepository.findById(testId);
        if (test.isPresent()) {
            return new TestDTO(test.get());
        } else {
            throw new EntityNotFoundException(EntityNotFoundException.Entity.TEST, testId);
        }
    }

    @DeleteMapping("/{testId}")
    public TestSuiteDTO deleteTest(
        @PathVariable() Long testId
    ) {
        return new TestSuiteDTO(testService.deleteTest(testId));
    }

    @PostMapping("")
    public TestDTO createTest(@Valid @RequestBody TestDTO dto) {
        Test test = new Test();
        test.setName(dto.getName());
        testSuiteRepository.findById(dto.getSuiteId()).ifPresentOrElse(test::setTestSuite, () -> {
            throw new EntityNotFoundException(TEST_SUITE, dto.getSuiteId());
        });

        Test savedTest = testRepository.save(test);
        return new TestDTO(savedTest);
    }


    @PostMapping("/{testId}/run")
    public TestExecutionResultDTO runTest(
        @PathVariable() Long testId
    ) {
        return testService.runTest(testId);
    }

    @PutMapping("")
    public Optional<TestDTO> saveTest(
        @RequestBody TestDTO dto
    ) {
        return testService.saveTest(dto);
    }


    @GetMapping("/editorConfig")
    public TestEditorConfigDTO getTestEditorConfig() {
        return new TestEditorConfigDTO();
    }


}
