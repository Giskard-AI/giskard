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
import java.util.Collection;
import java.util.Collections;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TestFunctionController {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final TestFunctionService testFunctionService;

    @GetMapping("/test-functions/{testId}")
    @Transactional(readOnly = true)
    public TestFunctionDTO getTestFunction(@PathVariable("testId") @NotNull UUID modelId) {
        return giskardMapper.toDTO(testFunctionRepository.getById(modelId));
    }

    @PostMapping("/test-functions")
    @Transactional
    public TestFunctionDTO getTestFunction(@Valid @RequestBody TestFunctionDTO testFunction) {
        return testFunctionService.save(testFunction);
    }

    @PostMapping("/test-functions/registry")
    @Transactional
    public void getTestFunction(@Valid @RequestBody Collection<TestFunctionDTO> testFunctions) {
        testFunctionService.saveAll(testFunctions);
    }

}
