package ai.giskard.web.rest.controllers;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.Project;
import ai.giskard.domain.SlicingFunction;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.service.SlicingFunctionService;
import ai.giskard.service.TestArgumentService;
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
import java.util.Collections;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

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
    private final TestArgumentService testArgumentService;

    @GetMapping("/slices/{uuid}")
    @Transactional(readOnly = true)
    public SlicingFunctionDTO getSlicingFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(slicingFunctionRepository.getById(uuid));
    }

    @PostMapping("/slices/{sliceFnUuid}/dataset/{datasetUuid}")
    @Transactional(readOnly = true)
    public SlicingResultDTO runAdHocFunction(@PathVariable("sliceFnUuid") @NotNull UUID sliceFnUuid,
                                             @PathVariable("datasetUuid") @NotNull UUID datasetUuid,
                                             @RequestBody Map<String, String> inputs) {
        SlicingFunction slicingFunction = slicingFunctionRepository.getById(sliceFnUuid);
        Dataset dataset = datasetRepository.getById(datasetUuid);
        Project project = dataset.getProject();

        try (MLWorkerClient client = mlWorkerService.createClient(project.isUsingInternalWorker())) {
            Map<String, String> argumentTypes = slicingFunction.getArgs().stream()
                .collect(Collectors.toMap(FunctionArgument::getName, FunctionArgument::getType));

            RunAdHocSlicingRequest.Builder builder = RunAdHocSlicingRequest.newBuilder()
                .setSlicingFunctionUuid(slicingFunction.getUuid().toString())
                .setDataset(ArtifactRef.newBuilder()
                    .setId(dataset.getId().toString())
                    .setProjectKey(dataset.getProject().getKey())
                    .build());

            for (Map.Entry<String, String> entry : inputs.entrySet()) {
                builder.addArguments(testArgumentService
                    .buildTestArgument(argumentTypes, entry.getKey(), entry.getValue(), project.getKey(), Collections.emptyList()));
            }

            SlicingResultMessage slicingResultMessage = client.getBlockingStub().runAdHocSlicing(builder.build());

            return convertGRPCObject(slicingResultMessage, SlicingResultDTO.class);
        }
    }

    @PutMapping("/slices/{uuid}")
    @Transactional
    public SlicingFunctionDTO updateSlicingFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                    @Valid @RequestBody SlicingFunctionDTO slicingFunction) {
        return slicingFunctionService.save(slicingFunction);
    }

}
