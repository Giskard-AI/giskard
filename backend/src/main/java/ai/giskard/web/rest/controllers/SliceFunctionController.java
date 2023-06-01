package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.SliceFunctionRepository;
import ai.giskard.service.SliceFunctionService;
import ai.giskard.web.dto.SliceFunctionDTO;
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
public class SliceFunctionController {

    private final GiskardMapper giskardMapper;
    private final SliceFunctionRepository sliceFunctionRepository;
    private final SliceFunctionService sliceFunctionService;

    @GetMapping("/slices/{uuid}")
    @Transactional(readOnly = true)
    public SliceFunctionDTO getTestFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(sliceFunctionRepository.getById(uuid));
    }

    @PutMapping("/slices/{uuid}")
    @Transactional
    public SliceFunctionDTO updateTestFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                               @Valid @RequestBody SliceFunctionDTO sliceFunction) {
        return sliceFunctionService.save(sliceFunction);
    }

}
