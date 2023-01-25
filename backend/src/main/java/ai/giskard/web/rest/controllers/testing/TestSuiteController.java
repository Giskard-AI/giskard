package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.TestSuiteNew;
import ai.giskard.repository.ml.TestSuiteNewRepository;
import ai.giskard.service.TestSuiteService;
import ai.giskard.web.dto.TestSuiteNewDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteController {
    private final TestSuiteService testSuiteService;
    private final GiskardMapper giskardMapper;
    private final TestSuiteNewRepository testSuiteNewRepository;

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

    @PostMapping("project/{projectId}/suite-new/{suiteId}/schedule-execution")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public ResponseEntity<Void> scheduleTestSuiteExecution(@PathVariable("projectId") @NotNull Long projectId,
                                                           @PathVariable("suiteId") @NotNull Long suiteId,
                                                           @Valid @RequestBody Map<@NotBlank String, @NotNull String> inputs) {
        testSuiteService.scheduleTestSuiteExecution(projectId, suiteId, inputs);

        return ResponseEntity.noContent().build();
    }

}
