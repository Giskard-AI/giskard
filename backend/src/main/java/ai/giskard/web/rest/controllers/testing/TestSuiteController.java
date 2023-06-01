package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuiteNew;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteNewRepository;
import ai.giskard.service.TestService;
import ai.giskard.service.TestSuiteExecutionService;
import ai.giskard.service.TestSuiteService;
import ai.giskard.web.dto.TestSuiteCompleteDTO;
import ai.giskard.web.dto.TestSuiteNewDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;
import java.util.UUID;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteController {
    private final TestSuiteService testSuiteService;
    private final TestService testService;
    private final GiskardMapper giskardMapper;
    private final TestSuiteNewRepository testSuiteNewRepository;
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;
    private final TestSuiteExecutionService testSuiteExecutionService;


    @PostMapping("project/{projectKey}/suites-new")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public Long saveTestSuite(@PathVariable("projectKey") @NotNull String projectKey, @Valid @RequestBody TestSuiteNewDTO dto) {
        TestSuiteNew savedSuite = testSuiteNewRepository.save(giskardMapper.fromDTO(dto));
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
    public TestSuiteNewDTO listTestSuiteComplete(@PathVariable("projectId") @NotNull Long projectId,
                                                 @PathVariable("suiteId") @NotNull Long suiteId) {
        return giskardMapper.toDTO(testSuiteNewRepository.findOneByProjectIdAndId(projectId, suiteId));
    }

    @GetMapping("project/{projectId}/suite-new/{suiteId}/complete")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional(readOnly = true)
    public TestSuiteCompleteDTO listTestSuiteNew(@PathVariable("projectId") @NotNull Long projectId,
                                                 @PathVariable("suiteId") @NotNull Long suiteId) {
        return new TestSuiteCompleteDTO(
            giskardMapper.toDTO(testSuiteNewRepository.findOneByProjectIdAndId(projectId, suiteId)),
            testService.listTestsFromRegistry(projectId),
            giskardMapper.datasetsToDatasetDTOs(datasetRepository.findAllByProjectId(projectId)),
            giskardMapper.modelsToModelDTOs(modelRepository.findAllByProjectId(projectId)),
            testSuiteExecutionService.listAllExecution(suiteId),
            testSuiteService.getSuiteInputs(projectId, suiteId)
        );
    }

    @PostMapping("project/{projectId}/suite-new/{suiteId}/schedule-execution")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public UUID scheduleTestSuiteExecution(@PathVariable("projectId") @NotNull Long projectId,
                                           @PathVariable("suiteId") @NotNull Long suiteId,
                                           @Valid @RequestBody Map<@NotBlank String, @NotNull String> inputs) {
        return testSuiteService.scheduleTestSuiteExecution(projectId, suiteId, inputs);
    }

    @PutMapping("project/{projectId}/suite-new/{suiteId}/test/{testId}/inputs")
    @PreAuthorize("@permissionEvaluator.canWriteProject(#projectId)")
    @Transactional
    public TestSuiteNewDTO updateTestInputs(@PathVariable("projectId") long projectId,
                                            @PathVariable("suiteId") long suiteId,
                                            @PathVariable("testId") @NotBlank String testId,
                                            @Valid @RequestBody Map<@NotBlank String, @NotNull String> inputs) {
       return testSuiteService.updateTestInputs(suiteId, testId, inputs);
    }

}
