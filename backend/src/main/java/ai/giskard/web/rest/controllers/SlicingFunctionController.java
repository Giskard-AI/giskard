package ai.giskard.web.rest.controllers;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.service.SlicingFunctionService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.SlicingResultDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.RunAdHocSlicingRequest;
import ai.giskard.worker.SlicingResultMessage;
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
public class SlicingFunctionController {

    private final GiskardMapper giskardMapper;
    private final SlicingFunctionRepository slicingFunctionRepository;
    private final DatasetRepository datasetRepository;
    private final MLWorkerService mlWorkerService;
    private final SlicingFunctionService slicingFunctionService;

    @GetMapping("/slices/{uuid}")
    @Transactional(readOnly = true)
    public SlicingFunctionDTO getTestFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(slicingFunctionRepository.getById(uuid));
    }

    @GetMapping("/slices/{sliceFnUuid}/dataset/{datasetUuid}")
    @Transactional(readOnly = true)
    public SlicingResultDTO runAdHocTest(@PathVariable("sliceFnUuid") @NotNull UUID sliceFnUuid,
                                         @PathVariable("datasetUuid") @NotNull UUID datasetUuid) {
        SlicingFunction slicingFunction = slicingFunctionRepository.getById(sliceFnUuid);
        Dataset dataset = datasetRepository.getById(datasetUuid);

        try (MLWorkerClient client = mlWorkerService.createClient(dataset.getProject().isUsingInternalWorker())) {
            RunAdHocSlicingRequest request = RunAdHocSlicingRequest.newBuilder()
                .setSlicingFunctionUuid(slicingFunction.getUuid().toString())
                .setDataset(ArtifactRef.newBuilder()
                    .setId(dataset.getId().toString())
                    .setProjectKey(dataset.getProject().getKey())
                    .build())
                .build();

            SlicingResultMessage slicingResultMessage = client.getBlockingStub().runAdHocSlicing(request);

            return convertGRPCObject(slicingResultMessage, SlicingResultDTO.class);
        }
    }

    @PutMapping("/slices/{uuid}")
    @Transactional
    public SlicingFunctionDTO updateTestFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                 @Valid @RequestBody SlicingFunctionDTO slicingFunction) {
        return slicingFunctionService.save(slicingFunction);
    }

}
