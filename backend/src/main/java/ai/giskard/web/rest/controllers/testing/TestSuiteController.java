package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestSuiteNew;
import ai.giskard.domain.ml.testing.Test;
import ai.giskard.repository.ml.TestRepository;
import ai.giskard.repository.ml.TestSuiteNewRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.TestSuiteService;
import ai.giskard.web.dto.TestSuiteCreateDTO;
import ai.giskard.web.dto.TestSuiteNewDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.*;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;

import static ai.giskard.web.rest.errors.Entity.TEST_SUITE;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteController {
    private final TestSuiteRepository testSuiteRepository;
    private final TestRepository testRepository;
    private final TestSuiteService testSuiteService;
    private final TestService testService;
    private final GiskardMapper giskardMapper;
    private final TestSuiteNewRepository testSuiteNewRepository;


    @PutMapping("suites/update_params")
    @Transactional
    public TestSuiteDTO updateTestSuiteParams(@Valid @RequestBody UpdateTestSuiteParamsDTO dto) {
        TestSuite suite;
        if (dto.getTestId() != null) {
            Test test = testRepository.getById(dto.getTestId());
            suite = test.getTestSuite();
        } else if (dto.getTestSuiteId() != null) {
            suite = testSuiteRepository.getById(dto.getTestSuiteId());
        } else {
            throw new IllegalArgumentException("Either test_id or test_suite_id should be specified");
        }

        suite = testSuiteService.updateTestSuite(new UpdateTestSuiteDTO(
            suite.getId(),
            suite.getName(),
            dto.getReferenceDatasetId() != null ? dto.getReferenceDatasetId() : suite.getReferenceDataset().getId(),
            dto.getActualDatasetId() != null ? dto.getActualDatasetId() : suite.getActualDataset().getId(),
            dto.getModelId() != null ? dto.getModelId() : suite.getModel().getId()
        ));
        return giskardMapper.testSuiteToTestSuiteDTO(suite);
    }

    @PutMapping("suites")
    @Transactional
    public TestSuiteDTO saveTestSuite(@Valid @RequestBody UpdateTestSuiteDTO dto) {
        TestSuite testSuite = testSuiteService.updateTestSuite(dto);
        return giskardMapper.testSuiteToTestSuiteDTO(testSuite);
    }


    @PostMapping("project/{projectKey}/suites-new")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public Long saveTestSuite(@PathVariable("projectKey") @NotNull String projectKey,
                              @Valid @RequestBody TestSuiteNewDTO dto,
                              @RequestParam(defaultValue = "false") boolean shouldGenerateTests) {
        TestSuiteNew savedSuite = testSuiteNewRepository.save(giskardMapper.fromDTO(dto));

        if (shouldGenerateTests) {
            // TODO: generate test automatically
        }

        return savedSuite.getId();
    }

    @GetMapping("project/{projectId}/suites-new")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public List<TestSuiteNewDTO> listTestSuitesNew(@PathVariable("projectId") @NotNull Long projectId) {
        return giskardMapper.toDTO(testSuiteNewRepository.findAllByProjectId(projectId));
    }

    @GetMapping("project/{projectId}/suite-new/{suiteId}")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public TestSuiteNewDTO listTestSuiteNew(@PathVariable("projectId") @NotNull Long projectId,
                                            @PathVariable("suiteId") @NotNull Long suiteId) {
        return giskardMapper.toDTO(testSuiteNewRepository.findOneByProjectIdAndId(projectId, suiteId));
    }

    @GetMapping("project/{projectId}/suite-new/{suiteId}/inputs")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public Map<String, String> getSuiteInputs(@PathVariable("projectId") @NotNull Long projectId,
                                              @PathVariable("suiteId") @NotNull Long suiteId) {
        return testSuiteService.getSuiteInputs(projectId, suiteId);
    }

    @PostMapping("project/{projectKey}/suites")
    public List<TestExecutionResultDTO> executeTestSuite(@Valid @RequestBody ExecuteTestSuiteRequest request) {
        return testService.executeTestSuite(request.getSuiteId());
    }

    @PostMapping("suites")
    @PreAuthorize("@permissionEvaluator.canWriteProject(#dto.projectId)")
    public TestSuiteDTO createTestSuite(@Valid @RequestBody TestSuiteCreateDTO dto) {
        TestSuite testSuite = giskardMapper.fromDTO(dto);
        return testSuiteService.createTestSuite(testSuite, dto.isShouldGenerateTests());
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
