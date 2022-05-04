package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.TestSuiteService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ExecuteTestSuiteRequest;
import ai.giskard.web.dto.ml.TestExecutionResultDTO;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

import static ai.giskard.web.rest.errors.Entity.*;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteController {
    private final TestSuiteRepository testSuiteRepository;
    private final ProjectRepository projectRepository;
    private final ModelRepository modelRepository;
    private final TestSuiteService testSuiteService;
    private final TestService testService;
    private final GiskardMapper giskardMapper;


    @PutMapping("suites")
    public TestSuiteDTO saveCodeBasedTestPreset(@Valid @RequestBody TestSuiteDTO dto) {
        TestSuite testSuite = testSuiteService.updateTestSuite(dto);
        return giskardMapper.testSuiteToTestSuiteDTO(testSuite);
    }

    @PostMapping("suites/execute")
    public List<TestExecutionResultDTO> executeTestSuite(@Valid @RequestBody ExecuteTestSuiteRequest request) {
        return testService.executeTestSuite(request.getSuiteId());
    }

    @PostMapping("suites")
    public TestSuiteDTO createTestSuite(@Valid @RequestBody TestSuiteDTO dto) {
        TestSuite testSuite = new TestSuite();
        testSuite.setName(dto.getName());
        projectRepository.findById(dto.getProject().getId()).ifPresentOrElse(testSuite::setProject, () -> {
            throw new EntityNotFoundException(PROJECT, dto.getProject().getId());
        });
        modelRepository.findById(dto.getModel().getId()).ifPresentOrElse(testSuite::setModel, () -> {
            throw new EntityNotFoundException(PROJECT_MODEL, dto.getModel().getId());
        });
        TestSuite savedTestSuite = testSuiteRepository.save(testSuite);
        return giskardMapper.testSuiteToTestSuiteDTO(savedTestSuite);
    }

    @GetMapping("suites/{projectId}")
    public List<TestSuiteDTO> listSuites(@PathVariable Long projectId) {
        List<TestSuite> listTestSuite = testSuiteRepository.findAllByProjectId(projectId);
        return giskardMapper.testSuitesToTestSuiteDTOs(listTestSuite);
    }

    @GetMapping("suite/{suiteId}")
    public TestSuiteDTO getTestSuite(@PathVariable Long suiteId) {
        TestSuite testSuite = testSuiteRepository.findById(suiteId).orElseThrow(() -> new EntityNotFoundException(TEST_SUITE, suiteId));
        return giskardMapper.testSuiteToTestSuiteDTO(testSuite);

    }

    @DeleteMapping("suite/{suiteId}")
    public void deleteTestSuite(@PathVariable Long suiteId) {
        testSuiteService.deleteSuite(suiteId);
    }

}
