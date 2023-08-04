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
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TestFunctionController {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final TestFunctionService testFunctionService;

    @GetMapping({"/tests/{testUuid}", "/project/{projectKey}/tests/{testUuid}"})
    @Transactional(readOnly = true)
    public TestFunctionDTO getTestFunction(@PathVariable("testUuid") @NotNull UUID testUuid) {
        return giskardMapper.toDTO(testFunctionRepository.getMandatoryById(testUuid));
    }

    @PutMapping({"/tests/{testUuid}", "/project/{projectKey}/tests/{testUuid}"})
    @Transactional
    public TestFunctionDTO updateTestFunction(@PathVariable("testUuid") @NotNull UUID testUuid,
                                              @Valid @RequestBody TestFunctionDTO testFunction) {
        return testFunctionService.save(testFunction);
    }

}
