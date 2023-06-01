package ai.giskard.web.rest.controllers;

import ai.giskard.domain.SliceFunction;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.SliceFunctionRepository;
import ai.giskard.service.SliceFunctionService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.SliceFunctionDTO;
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
public class SliceFunctionController {

    private final GiskardMapper giskardMapper;
    private final SliceFunctionRepository sliceFunctionRepository;
    private final DatasetRepository datasetRepository;
    private final MLWorkerService mlWorkerService;
    private final SliceFunctionService sliceFunctionService;

    @GetMapping("/slices/{uuid}")
    @Transactional(readOnly = true)
    public SliceFunctionDTO getTestFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(sliceFunctionRepository.getById(uuid));
    }

    @GetMapping("/slices/{sliceFnUuid}/dataset/{datasetUuid}")
    @Transactional(readOnly = true)
    public SlicingResultDTO runAdHocTest(@PathVariable("sliceFnUuid") @NotNull UUID sliceFnUuid,
                                         @PathVariable("datasetUuid") @NotNull UUID datasetUuid) {
        SliceFunction sliceFunction = sliceFunctionRepository.getById(sliceFnUuid);
        Dataset dataset = datasetRepository.getById(datasetUuid);

        try (MLWorkerClient client = mlWorkerService.createClient(dataset.getProject().isUsingInternalWorker())) {
            RunAdHocSlicingRequest request = RunAdHocSlicingRequest.newBuilder()
                .setSlicingFunctionUuid(sliceFunction.getUuid().toString())
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
    public SliceFunctionDTO updateTestFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                               @Valid @RequestBody SliceFunctionDTO sliceFunction) {
        return sliceFunctionService.save(sliceFunction);
    }

}
