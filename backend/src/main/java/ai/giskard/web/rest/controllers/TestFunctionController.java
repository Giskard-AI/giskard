package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.TestFunctionService;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TestFunctionController {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final TestFunctionService testFunctionService;

    @GetMapping("/tests")
    @Transactional(readOnly = true)
    public List<TestFunctionDTO> findAll() {
        return testFunctionService.findAll();
    }
    @GetMapping("/tests/{testUuid}")
    @Transactional(readOnly = true)
    public TestFunctionDTO getTestFunction(@PathVariable("testUuid") @NotNull UUID testUuid) {
        return giskardMapper.toDTO(testFunctionRepository.getById(testUuid));
    }

    @PutMapping("/tests/{testUuid}")
    @Transactional
    public TestFunctionDTO updateTestFunction(@PathVariable("testUuid") @NotNull UUID testUuid,
                                              @Valid @RequestBody TestFunctionDTO testFunction) {
        return testFunctionService.save(testFunction);
    }

    @PostMapping("/tests/registry")
    @Transactional
    public void getTestFunction(@Valid @RequestBody Collection<TestFunctionDTO> testFunctions) {
        testFunctionService.saveAll(testFunctions);
    }

}
