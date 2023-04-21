package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.InspectionService;
import ai.giskard.service.ModelService;
import ai.giskard.web.dto.InspectionCreateDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.InspectionDTO;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class InspectionController {

    private final InspectionService inspectionService;
    private final ModelService modelService;
    private final InspectionRepository inspectionRepository;
    private final GiskardMapper giskardMapper;
    private final PermissionEvaluator permissionEvaluator;
    private final ModelRepository modelRepository;
    private final DatasetRepository datasetRepository;


    /**
     * get all inspections
     *
     * @return list of inspections
     */
    @GetMapping("/inspections")
    public List<InspectionDTO> getInspections() {
        return giskardMapper.inspectionsToInspectionDTOs(inspectionService.getInspections());
    }

    /**
     * get all inspections for a project
     *
     * @param projectId id of the project
     * @return list of inspections
     */
    @GetMapping("project/{projectId}/inspections")
    public List<InspectionDTO> listProjectInspections(@PathVariable @NotNull long projectId) {
        return giskardMapper.inspectionsToInspectionDTOs(inspectionService.getInspectionsByProjectId(projectId));
    }

    @GetMapping("/inspection/{id}")
    public InspectionDTO getInspection(@PathVariable @NotNull Long id) {
        Inspection inspection = inspectionRepository.getMandatoryById(id);
        return giskardMapper.toDTO(inspection);
    }


    /**
     * get the labels for the target column
     *
     * @param inspectionId id of the inspection
     * @return List of labels
     */
    @GetMapping("/inspection/{inspectionId}/labels")
    public List<String> getLabels(@PathVariable @NotNull Long inspectionId) {
        return inspectionService.getLabels(inspectionId);
    }

    @PostMapping("/inspection")
    public InspectionDTO createInspection(@RequestBody @NotNull InspectionCreateDTO createDTO) {
        return giskardMapper.toDTO(modelService.createInspection(createDTO.getName(), createDTO.getModelId(), createDTO.getDatasetId(), createDTO.isSample()));
    }

    /**
     * delete an inspection
     *
     * @param id id of the inspection
     */
    @DeleteMapping("/inspections/{id}")
    public void deleteInspection(@PathVariable @NotNull Long id) {
        inspectionService.deleteInspection(id);
    }

    /**
     * @param id
     * @param createDTO
     * @return updated inspection
     * @throws EntityNotFoundException
     */
    @PutMapping("/inspections/{id}")
    public InspectionDTO updateInspection(@PathVariable @NotNull Long id, @RequestBody @NotNull InspectionCreateDTO createDTO) throws EntityNotFoundException {
        return giskardMapper.toDTO(inspectionService.updateInspection(id, createDTO));
    }

    @GetMapping("/suggest/{modelId}/{datasetId}/{idx}")
    public void getSuggestions(@PathVariable @NotNull UUID modelId, @PathVariable @NotNull UUID datasetId, @PathVariable @NotNull int idx) {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Dataset dataset = datasetRepository.getById(datasetId);
        inspectionService.getSuggestions(
            model,
            dataset,
            idx
        );
    }
}
