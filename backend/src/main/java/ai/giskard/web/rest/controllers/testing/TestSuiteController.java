package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.service.TestSuiteExecutionService;
import ai.giskard.service.TestSuiteService;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteController {
    private final TestSuiteService testSuiteService;
    private final GiskardMapper giskardMapper;
    private final TestSuiteRepository testSuiteRepository;
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;
    private final TestSuiteExecutionService testSuiteExecutionService;

    @PostMapping("project/{projectKey}/suites")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public Long saveTestSuite(@PathVariable("projectKey") @NotNull String projectKey, @Valid @RequestBody TestSuiteDTO dto) {
        return testSuiteService.saveTestSuite(projectKey, dto);
    }

    @PostMapping("project/{projectKey}/suites/generate")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public Long generateTestSuite(@PathVariable("projectKey") @NotNull String projectKey,
                                  @Valid @RequestBody GenerateTestSuiteDTO dto) {
        return testSuiteService.generateTestSuite(projectKey, dto);
    }

    @GetMapping("project/{projectId}/suites")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public List<TestSuiteDTO> listTestSuites(@PathVariable("projectId") @NotNull Long projectId) {
        List<TestSuite> allByProjectId = testSuiteRepository.findAllByProjectId(projectId);
        return giskardMapper.toDTO(allByProjectId);
    }

    @GetMapping("project/{projectId}/suite/{suiteId}")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public TestSuiteDTO listTestSuite(@PathVariable("projectId") @NotNull Long projectId,
                                      @PathVariable("suiteId") @NotNull Long suiteId) {
        return giskardMapper.toDTO(testSuiteRepository.findOneByProjectIdAndId(projectId, suiteId));
    }

    @PutMapping("project/{projectKey}/suite/{suiteId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public TestSuiteDTO updateTestSuite(@PathVariable("projectKey") @NotBlank String projectKey,
                                        @PathVariable("suiteId") long suiteId,
                                        @RequestBody TestSuiteDTO testSuiteDTO) {
        return testSuiteService.updateTestSuite(suiteId, testSuiteDTO);
    }

    @DeleteMapping("project/{projectKey}/suite/{suiteId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public ResponseEntity<Void> deleteTestSuite(@PathVariable("projectKey") @NotBlank String projectKey,
                                                @PathVariable("suiteId") long suiteId) {
        testSuiteService.deleteTestSuite(suiteId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("project/{projectId}/suite/{suiteId}/complete")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public TestSuiteCompleteDTO listTestSuiteComplete(@PathVariable("projectId") @NotNull Long projectId,
                                                      @PathVariable("suiteId") @NotNull Long suiteId) {
        return new TestSuiteCompleteDTO(
            giskardMapper.toDTO(testSuiteRepository.findOneByProjectIdAndId(projectId, suiteId)),
            giskardMapper.datasetsToDatasetDTOs(datasetRepository.findAllByProjectId(projectId)),
            giskardMapper.modelsToModelDTOs(modelRepository.findAllByProjectId(projectId)),
            testSuiteExecutionService.listAllExecution(suiteId),
            testSuiteService.getSuiteInputs(projectId, suiteId)
        );
    }

    @PostMapping("project/{projectId}/suite/{suiteId}/test")
    @PreAuthorize("@permissionEvaluator.canWriteProjectId(#projectId)")
    @Transactional
    public TestSuiteDTO addTestToSuite(@PathVariable("projectId") long projectId,
                                       @PathVariable("suiteId") long suiteId,
                                       @Valid @RequestBody SuiteTestDTO suiteTest) {
        return giskardMapper.toDTO(testSuiteService.addTestToSuite(suiteId, suiteTest));
    }

    @PostMapping("project/{projectId}/suite/{suiteId}/schedule-execution")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    public UUID scheduleTestSuiteExecution(@PathVariable("projectId") @NotNull Long projectId,
                                           @PathVariable("suiteId") @NotNull Long suiteId,
                                           @Valid @RequestBody List<FunctionInputDTO> inputs) {
        return testSuiteService.scheduleTestSuiteExecution(projectId, suiteId, inputs);
    }

    @PostMapping("project/{projectId}/suite/{suiteId}/try")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    public TestSuiteExecutionDTO tryTestSuite(@PathVariable("projectId") @NotNull Long projectId,
                                              @PathVariable("suiteId") @NotNull Long suiteId,
                                              @Valid @RequestBody List<FunctionInputDTO> inputs) {
        TestSuite testSuite = testSuiteService.getInitialized(suiteId);
        Map<String, String> suiteInputs = testSuiteService.getSuiteInputs(projectId, suiteId);

        return giskardMapper.toDTO(testSuiteService.tryTestSuiteExecution(testSuite, suiteInputs, inputs));

    }


    @PutMapping("project/{projectId}/suite/{suiteId}/test/{testId}/inputs")
    @PreAuthorize("@permissionEvaluator.canWriteProjectId(#projectId)")
    @Transactional
    public TestSuiteDTO updateTestInputs(@PathVariable("projectId") long projectId,
                                         @PathVariable("suiteId") long suiteId,
                                         @PathVariable("testId") long testId,
                                         @Valid @RequestBody List<@Valid FunctionInputDTO> inputs) {
        return testSuiteService.updateTestInputs(suiteId, testId, inputs);
    }

    @DeleteMapping("project/{projectKey}/suite/{suiteId}/suite-test/{suiteTestId}")
    @PreAuthorize("@permissionEvaluator.canReadProjectKey(#projectKey)")
    @Transactional
    public TestSuiteDTO updateTestInputs(@PathVariable("projectKey") String projectKey,
                                         @PathVariable("suiteId") long suiteId,
                                         @PathVariable("suiteTestId") long suiteTestId) {
        return testSuiteService.removeSuiteTest(suiteId, suiteTestId);
    }


}
