package ai.giskard.web.rest.controllers;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.service.TransformationFunctionService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.TransformationResultDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.RunAdHocTransformationRequest;
import ai.giskard.worker.TransformationResultMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.UUID;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class TransformationFunctionController {

    private final GiskardMapper giskardMapper;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final DatasetRepository datasetRepository;
    private final MLWorkerService mlWorkerService;
    private final TransformationFunctionService transformationFunctionService;

    @GetMapping("/transformations/{uuid}")
    @Transactional(readOnly = true)
    public TransformationFunctionDTO getTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(transformationFunctionRepository.getById(uuid));
    }

    @GetMapping("/transformations/{transformationFnUuid}/dataset/{datasetUuid}")
    @Transactional(readOnly = true)
    public TransformationResultDTO runAdHocTransformation(@PathVariable("transformationFnUuid") @NotNull UUID sliceFnUuid,
                                                          @PathVariable("datasetUuid") @NotNull UUID datasetUuid) {
        TransformationFunction transformationFunction = transformationFunctionRepository.getById(sliceFnUuid);
        Dataset dataset = datasetRepository.getById(datasetUuid);

        try (MLWorkerClient client = mlWorkerService.createClient(dataset.getProject().isUsingInternalWorker())) {
            RunAdHocTransformationRequest request = RunAdHocTransformationRequest.newBuilder()
                .setTransformationFunctionUuid(transformationFunction.getUuid().toString())
                .setDataset(ArtifactRef.newBuilder()
                    .setId(dataset.getId().toString())
                    .setProjectKey(dataset.getProject().getKey())
                    .build())
                .build();

            TransformationResultMessage transformationResultMessage = client.getBlockingStub().runAdHocTransformation(request);

            return convertGRPCObject(transformationResultMessage, TransformationResultDTO.class);
        }
    }

    @PutMapping("/transformations/{uuid}")
    @Transactional
    public TransformationFunctionDTO updateTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                                  @Valid @RequestBody TransformationFunctionDTO transformationFunction) {
        return transformationFunctionService.save(transformationFunction);
    }

}
