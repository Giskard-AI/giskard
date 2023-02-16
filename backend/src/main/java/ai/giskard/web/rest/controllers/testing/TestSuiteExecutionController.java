package ai.giskard.web.rest.controllers.testing;

import ai.giskard.service.TestSuiteExecutionService;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;


@RestController
@RequestMapping("/api/v2/testing/")
@RequiredArgsConstructor
public class TestSuiteExecutionController {

    private final TestSuiteExecutionService testSuiteExecutionService;

    @GetMapping("project/{projectId}/suite-new/{suiteId}/execution")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    @Transactional
    public List<TestSuiteExecutionDTO> listSuiteExecutions(@PathVariable("projectId") @NotNull Long projectId,
                                                           @PathVariable("suiteId") @NotNull Long suiteId) {
        return testSuiteExecutionService.listAllExecution(suiteId);
    }

}
