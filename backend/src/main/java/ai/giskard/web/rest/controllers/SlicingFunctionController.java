package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.service.SlicingFunctionService;
import ai.giskard.web.dto.SlicingFunctionDTO;
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
public class SlicingFunctionController {

    private final GiskardMapper giskardMapper;
    private final SlicingFunctionRepository slicingFunctionRepository;
    private final SlicingFunctionService slicingFunctionService;

    @GetMapping("/slices/{uuid}")
    @Transactional(readOnly = true)
    public SlicingFunctionDTO getSlicingFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(slicingFunctionRepository.getMandatoryById(uuid));
    }

    @PutMapping("/slices/{uuid}")
    public SlicingFunctionDTO updateSlicingFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                    @Valid @RequestBody SlicingFunctionDTO slicingFunction) {
        return slicingFunctionService.save(slicingFunction);
    }

}
