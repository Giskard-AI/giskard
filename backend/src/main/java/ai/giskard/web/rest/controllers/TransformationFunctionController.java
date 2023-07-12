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
import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TransformationFunctionController {

    private final GiskardMapper giskardMapper;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final TransformationFunctionService transformationFunctionService;

    @GetMapping({"project/{projectKey}/transformations/{uuid}", "/transformations/{uuid}"})
    @Transactional(readOnly = true)
    public TransformationFunctionDTO getTransformationFunction(
        @PathVariable(value = "projectKey", required = false) String projectKey,
        @PathVariable("uuid") @NotNull UUID uuid) {
        // TODO GSK-1280: add projectKey to slicing function
        return giskardMapper.toDTO(transformationFunctionRepository.getMandatoryById(uuid));
    }

    @PutMapping({"project/{projectKey}/transformations/{uuid}", "/transformations/{uuid}"})
    @Transactional
    public TransformationFunctionDTO updateTransformationFunction(
        @PathVariable(value = "projectKey", required = false) String projectKey,
        @PathVariable("uuid") @NotNull UUID uuid,
        @Valid @RequestBody TransformationFunctionDTO transformationFunction) {
        transformationFunction.setProjectKeys(List.of(projectKey));
        return transformationFunctionService.save(transformationFunction);
    }

}
