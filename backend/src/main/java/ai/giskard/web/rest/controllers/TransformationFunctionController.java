package ai.giskard.web.rest.controllers;

import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.service.TransformationFunctionService;
import ai.giskard.web.dto.TransformationFunctionDTO;
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
public class TransformationFunctionController {

    private final GiskardMapper giskardMapper;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final TransformationFunctionService transformationFunctionService;

    @GetMapping("/transformations/{uuid}")
    @Transactional(readOnly = true)
    public TransformationFunctionDTO getTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(transformationFunctionRepository.getMandatoryById(uuid));
    }

    @PutMapping("/transformations/{uuid}")
    @Transactional
    public TransformationFunctionDTO updateTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                                  @Valid @RequestBody TransformationFunctionDTO transformationFunction) {
        return transformationFunctionService.save(transformationFunction);
    }

}
