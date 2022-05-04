package ai.giskard.web.rest.controllers.testing;

import ai.giskard.domain.ml.testing.CodeBasedTestPreset;
import ai.giskard.domain.ml.TestType;
import ai.giskard.repository.ml.CodeBasedTestPresetRepository;
import ai.giskard.service.UsernameAlreadyUsedException;
import ai.giskard.web.dto.ml.CodeBasedTestPresetDTO;
import org.apache.commons.lang3.NotImplementedException;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/api/v2/testing/preset")
public class TestPresetController {
    private final CodeBasedTestPresetRepository codeBasedTestPresetRepository;

    public TestPresetController(CodeBasedTestPresetRepository codeBasedTestPresetRepository) {
        this.codeBasedTestPresetRepository = codeBasedTestPresetRepository;
    }

    @GetMapping("/")
    public List<CodeBasedTestPreset> getTestPresets(@RequestParam(value = "type") TestType testType) {
        if (testType == TestType.CODE) {
            return codeBasedTestPresetRepository.findAll();
        } else {
            throw new NotImplementedException("only code based presets are available at the moment");
        }
    }

    @PostMapping("/presets/code")
    public CodeBasedTestPreset createCodeBasedTestPreset(@Valid @RequestBody CodeBasedTestPresetDTO testDTO) {
        testDTO.setId(null);
        return codeBasedTestPresetRepository.save(new CodeBasedTestPreset(testDTO));
    }

    @PutMapping("/presets/code")
    public CodeBasedTestPreset updateCodeBasedTestPreset(@Valid @RequestBody CodeBasedTestPresetDTO testDTO) {
        codeBasedTestPresetRepository
            .findById(testDTO.getId())
            .ifPresent(existingUser -> {
                throw new UsernameAlreadyUsedException();
            });
        return codeBasedTestPresetRepository.save(new CodeBasedTestPreset(testDTO));
    }

}
