package ai.giskard.web.rest.testing;

import ai.giskard.domain.ml.testing.Test;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.dto.ml.TestDTO;
import ai.giskard.service.dto.ml.TestEditorConfigDTO;
import ai.giskard.service.dto.ml.TestExecutionResultDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2/testing/tests")
public class TestController {
    private final TestRepository testRepository;
    private final TestService testService;
    private final TestSuiteRepository testSuiteRepository;

    public TestController(TestService testService, TestSuiteRepository testSuiteRepository, TestRepository testRepository) {
        this.testService = testService;
        this.testSuiteRepository = testSuiteRepository;
        this.testRepository = testRepository;
    }

    @PostMapping("")
    private TestDTO createTest(@RequestBody TestDTO dto) {
        Test test = new Test();
        test.setName(dto.getName());
        test.setCode(dto.getCode());
        testSuiteRepository.findById(dto.getTestSuiteId()).ifPresent(test::setTestSuite);
        Test saved = testRepository.save(test);
        return new TestDTO(saved);

    }

    @GetMapping("")
    public List<TestDTO> getTests(
        @RequestParam Long suiteId
    ) {
        return testRepository.findAllByTestSuiteId(suiteId).stream()
            .map(TestDTO::new).collect(Collectors.toList());
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
