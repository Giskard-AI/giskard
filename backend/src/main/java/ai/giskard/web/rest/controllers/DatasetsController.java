package ai.giskard.web.rest.controllers;

import ai.giskard.domain.*;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.*;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.utils.FunctionArguments;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import com.fasterxml.jackson.core.JsonProcessingException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

import static ai.giskard.ml.dto.MLWorkerWSUtils.convertMLWorkerWSObject;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class DatasetsController {
    private final Logger log = LoggerFactory.getLogger(DatasetsController.class);

    private final DatasetRepository datasetRepository;
    private final GiskardMapper giskardMapper;
    private final DatasetService datasetService;
    private final ProjectRepository projectRepository;
    private final ProjectFileDeletionService deletionService;
    private final UsageService usageService;
    private final SlicingFunctionService slicingFunctionService;
    private final TransformationFunctionService transformationFunctionService;
    private final MLWorkerService mlWorkerService;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final TestArgumentService testArgumentService;

    /**
     * Retrieve the list of datasets from the specified project
     * Returns all the project's datasets if the user is admin, project's owner or in project's guest list
     *
     * @param projectId id of the project
     * @return List of datasets
     */
    @GetMapping("project/{projectId}/datasets")
    public List<DatasetDTO> listProjectDatasets(@PathVariable @NotNull Long projectId) {
        return giskardMapper.datasetsToDatasetDTOs(datasetRepository.findAllByProjectId(projectId));
    }

    @GetMapping("project/{projectKey}/datasets/{datasetId}")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public DatasetDTO getDatasetMeta(@PathVariable("projectKey") @NotNull String projectKey,
                                     @PathVariable("datasetId") @NotNull UUID datasetId) {
        return giskardMapper.datasetToDatasetDTO(datasetRepository.getMandatoryById(datasetId));
    }


    /**
     * Get the rows in the specified range
     *
     * @param datasetId id of the dataset
     * @return List of datasets
     */

    @PostMapping("/dataset/{datasetId}/rows")
    public DatasetPageDTO getRows(@PathVariable @NotNull UUID datasetId, @NotNull int offset, @NotNull int size,
                                  @RequestBody RowFilterDTO rowFilter,
                                  @RequestParam(required = false, defaultValue = "false") boolean shuffle,
                                  @RequestParam(required = false, defaultValue = "true") boolean sample) throws IOException {
        DatasetPageDTO rows = datasetService.getRows(datasetId, offset, offset + size, rowFilter, sample);

        if (shuffle) {
            rows.setContent(new ArrayList<>(rows.getContent()));
            Collections.shuffle(rows.getContent());
        }

        return rows;
    }

    @DeleteMapping("/dataset/{datasetId}")
    public MessageDTO deleteDataset(@PathVariable @NotNull UUID datasetId) {
        deletionService.deleteDataset(datasetId);
        return new MessageDTO("Dataset {} has been deleted", datasetId);
    }

    @GetMapping("/dataset/prepare-delete/{datasetId}")
    public PrepareDeleteDTO prepareDatasetDelete(@PathVariable @NotNull UUID datasetId) {
        return usageService.prepareDeleteDataset(datasetId);
    }

    @PostMapping("project/{projectKey}/datasets")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public void createDatasetMeta(@PathVariable("projectKey") @NotNull String projectKey, @RequestBody @NotNull DatasetDTO dto) {
        if (datasetRepository.existsById(dto.getId())) {
            log.info("Dataset already exists {}", dto.getId());
            return;
        }
        Project project = projectRepository.getOneByKey(projectKey);
        Dataset dataset = giskardMapper.fromDTO(dto);
        dataset.setProject(project);
        datasetRepository.save(dataset);
    }

    @PatchMapping("/dataset/{datasetId}/name/{name}")
    public DatasetDTO renameDataset(@PathVariable UUID datasetId, @PathVariable @Valid @NotBlank String name) {
        return giskardMapper.datasetToDatasetDTO(datasetService.renameDataset(datasetId, name));
    }

    @PostMapping("project/{projectId}/datasets/{datasetUuid}/process")
    @PreAuthorize("@permissionEvaluator.canReadProject(#projectId)")
    public DatasetProcessingResultDTO datasetProcessing(@PathVariable("projectId") @NotNull long projectId,
                                                        @PathVariable("datasetUuid") @NotNull UUID datasetUuid,
                                                        @RequestBody List<ParameterizedCallableDTO> processingFunctions,
                                                        @RequestParam(required = false, defaultValue = "true") boolean sample) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetUuid);
        Project project = dataset.getProject();

        Map<UUID, DatasetProcessFunction> callables = processingFunctions.stream()
            .map(processingFunction -> switch (processingFunction.getType()) {
                case "SLICING" -> slicingFunctionService.getInitialized(processingFunction.getUuid());
                case "TRANSFORMATION" -> transformationFunctionService.getInitialized(processingFunction.getUuid());
                default -> throw new IllegalStateException("Unexpected value: " + processingFunction.getType());
            })
            .collect(Collectors.toMap(Callable::getUuid, Function.identity(), (l, r) -> l));

        MLWorkerID workerID = project.isUsingInternalWorker() ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            List<MLWorkerWSDatasetProcessingFunctionDTO> functions =
                processingFunctions.stream().map(processingFunction -> {
                    MLWorkerWSDatasetProcessingFunctionDTO.MLWorkerWSDatasetProcessingFunctionDTOBuilder functionBuilder =
                        MLWorkerWSDatasetProcessingFunctionDTO.builder();

                    DatasetProcessFunction callable = callables.get(processingFunction.getUuid());
                    Map<String, FunctionArgument> arguments = callable.getArgs().stream()
                        .collect(Collectors.toMap(FunctionArgument::getName, Function.identity()));

                    if (callable.isCellLevel()) {
                        arguments.put("column_name", FunctionArguments.COLUMN_NAME);
                    }

                    MLWorkerWSArtifactRefDTO artifactRef = MLWorkerWSArtifactRefDTO.builder()
                        .id(callable.getUuid().toString())
                        .build();
                    if (callable.getProjectKey() != null) {
                        artifactRef.setProjectKey(callable.getProjectKey());
                    }

                    if (callable instanceof SlicingFunction) {
                        functionBuilder.slicingFunction(artifactRef);
                    } else {
                        functionBuilder.transformationFunction(artifactRef);
                    }

                    List<MLWorkerWSFuncArgumentDTO> argumentList = new ArrayList<>(processingFunction.getParams().size());
                    for (FunctionInputDTO input : processingFunction.getParams()) {
                            argumentList.add(testArgumentService
                                .buildTestArgumentWS(
                                    arguments,
                                    input.getName(),
                                    input.getValue(),
                                    project.getKey(),
                                    Collections.emptyList(),
                                    sample
                                )
                            );
                    }
                    functionBuilder.arguments(argumentList);

                    return functionBuilder.build();
                }).toList();

            MLWorkerWSDatasetProcessingParamDTO param = MLWorkerWSDatasetProcessingParamDTO.builder()
                .dataset(MLWorkerWSArtifactRefDTO.fromDataset(dataset))
                .functions(functions)
                .build();

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                workerID,
                MLWorkerWSAction.datasetProcessing,
                param
            );
            if (result instanceof MLWorkerWSDatasetProcessingDTO response) {
                response = (MLWorkerWSDatasetProcessingDTO) result;

                return convertMLWorkerWSObject(response, DatasetProcessingResultDTO.class);
            }
        }
        throw new NullPointerException("Dataset processing failed");
    }
}
