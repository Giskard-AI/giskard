package ai.giskard.web.rest.controllers;

import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.Project;
import ai.giskard.domain.TransformationFunction;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.service.TestArgumentService;
import ai.giskard.service.TransformationFunctionService;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.TransformationResultDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.ArtifactRef;
import ai.giskard.worker.RunAdHocTransformationRequest;
import ai.giskard.worker.TransformationResultMessage;
import lombok.RequiredArgsConstructor;
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
public class TransformationFunctionController {

    private final GiskardMapper giskardMapper;
    private final TransformationFunctionRepository transformationFunctionRepository;
    private final DatasetRepository datasetRepository;
    private final MLWorkerService mlWorkerService;
    private final TransformationFunctionService transformationFunctionService;
    private final TestArgumentService testArgumentService;

    @GetMapping("/transformations/{uuid}")
    public TransformationFunctionDTO getTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid) {
        return giskardMapper.toDTO(transformationFunctionRepository.getMandatoryById(uuid));
    }

    @PostMapping("/transformations/{transformationFnUuid}/dataset/{datasetUuid}")
    public TransformationResultDTO runAdHocTransformation(@PathVariable("transformationFnUuid") @NotNull UUID sliceFnUuid,
                                                          @PathVariable("datasetUuid") @NotNull UUID datasetUuid,
                                                          @RequestBody Map<String, String> inputs) {
        TransformationFunction transformationFunction = transformationFunctionRepository.getMandatoryById(sliceFnUuid);
        Dataset dataset = datasetRepository.getMandatoryById(datasetUuid);
        Project project = dataset.getProject();

        try (MLWorkerClient client = mlWorkerService.createClient(project.isUsingInternalWorker())) {
            Map<String, String> argumentTypes = transformationFunction.getArgs().stream()
                .collect(Collectors.toMap(FunctionArgument::getName, FunctionArgument::getType));

            RunAdHocTransformationRequest.Builder builder = RunAdHocTransformationRequest.newBuilder()
                .setTransformationFunctionUuid(transformationFunction.getUuid().toString())
                .setDataset(ArtifactRef.newBuilder()
                    .setId(dataset.getId().toString())
                    .setProjectKey(dataset.getProject().getKey())
                    .build());

            for (Map.Entry<String, String> entry : inputs.entrySet()) {
                builder.addArguments(testArgumentService
                    .buildTestArgument(argumentTypes, entry.getKey(), entry.getValue(), project.getKey(), Collections.emptyList()));
            }

            TransformationResultMessage transformationResultMessage = client.getBlockingStub().runAdHocTransformation(builder.build());

            return convertGRPCObject(transformationResultMessage, TransformationResultDTO.class);
        }
    }

    @PutMapping("/transformations/{uuid}")
    public TransformationFunctionDTO updateTransformationFunction(@PathVariable("uuid") @NotNull UUID uuid,
                                                                  @Valid @RequestBody TransformationFunctionDTO transformationFunction) {
        return transformationFunctionService.save(transformationFunction);
    }

}
