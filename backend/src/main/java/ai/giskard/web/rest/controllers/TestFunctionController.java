package ai.giskard.web.rest.controllers;

import ai.giskard.domain.TestFunction;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestFunctionService;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ModelDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TestFunctionController {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final TestFunctionService testFunctionService;

    @GetMapping("project/{projectKey}/test-functions/{testId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional(readOnly = true)
    public TestFunctionDTO getTestFunction(@PathVariable("projectKey") @NotNull String projectKey,
                                           @PathVariable("testId") @NotNull UUID modelId) {
        return giskardMapper.toDTO(testFunctionRepository.getById(modelId));
    }

    @PostMapping("project/{projectKey}/test-functions")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    @Transactional
    public TestFunctionDTO getTestFunction(@PathVariable("projectKey") @NotNull String projectKey,
                                           @Valid @RequestBody TestFunctionDTO testFunction) {
        return testFunctionService.save(testFunction);
    }

}
