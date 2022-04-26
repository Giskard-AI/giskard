package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.TestSuiteService;
import ai.giskard.service.dto.ml.ExecuteTestSuiteRequest;
import ai.giskard.service.dto.ml.TestExecutionResultDTO;
import ai.giskard.service.dto.ml.TestSuiteDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static ai.giskard.web.rest.errors.Entity.*;


@RestController
@RequestMapping("/api/v2/testing/")
public class TestSuiteController {
    private final TestSuiteRepository testSuiteRepository;
    private final ProjectRepository projectRepository;
    private final ModelRepository modelRepository;
    private final TestSuiteService testSuiteService;
    private final TestService testService;

    public TestSuiteController(TestSuiteRepository testSuiteRepository, ProjectRepository projectRepository,
                               ModelRepository modelRepository, TestSuiteService testSuiteService, TestService testService) {
        this.testSuiteRepository = testSuiteRepository;
        this.projectRepository = projectRepository;
        this.modelRepository = modelRepository;
        this.testSuiteService = testSuiteService;
        this.testService = testService;
    }

    @PutMapping("suites")
    public Optional<TestSuiteDTO> saveCodeBasedTestPreset(@Valid @RequestBody TestSuiteDTO dto) {
        return testSuiteService.updateTestSuite(dto);
    }

    @PostMapping("suites/execute")
    public List<TestExecutionResultDTO> executeTestSuite(@Valid @RequestBody ExecuteTestSuiteRequest request) {
        return testService.executeTestSuite(request.getSuiteId());
    }

    @PostMapping("suites")
    public TestSuiteDTO createTestSuite(@Valid @RequestBody TestSuiteDTO dto) {
        TestSuite testSuite = new TestSuite();
        testSuite.setName(dto.getName());
        projectRepository.findById(dto.getProjectId()).ifPresentOrElse(testSuite::setProject, () -> {
            throw new EntityNotFoundException(PROJECT, dto.getProjectId());
        });
        modelRepository.findById(dto.getModel().getId()).ifPresentOrElse(testSuite::setModel, () -> {
            throw new EntityNotFoundException(PROJECT_MODEL, dto.getModel().getId());
        });
        TestSuite savedTestSuite = testSuiteRepository.save(testSuite);
        return new TestSuiteDTO(savedTestSuite);
    }

    @GetMapping("suites/{projectId}")
    public List<TestSuiteDTO> listSuites(@PathVariable Long projectId) {
        return testSuiteRepository.findAllByProjectId(projectId).stream().map(TestSuiteDTO::new).collect(Collectors.toList());
    }

    @GetMapping("suite/{suiteId}")
    public TestSuiteDTO getTestSuite(@PathVariable Long suiteId) {
        Optional<TestSuite> testSuite = testSuiteRepository.findById(suiteId);
        if (testSuite.isPresent()) {
            return new TestSuiteDTO(testSuite.get());
        } else {
            throw new EntityNotFoundException(TEST_SUITE, suiteId);
        }
    }
    @DeleteMapping("suite/{suiteId}")
    public void deleteTestSuite(@PathVariable Long suiteId) {
        testSuiteService.deleteSuite(suiteId);
    }

}
