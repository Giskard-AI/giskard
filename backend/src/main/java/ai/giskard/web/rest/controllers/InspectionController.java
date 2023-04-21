package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.InspectionService;
import ai.giskard.service.ModelService;
import ai.giskard.web.dto.InspectionCreateDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.InspectionDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.RandomUtils;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.io.IOException;
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
     * Retrieve the row specified by the given range on the dataset
     * TODO Replace with spring pagination
     *
     * @param inspectionId id of the inspection
     * @param filter       filter parameters object
     * @param rangeMin     minimum range
     * @param rangeMax     maximum range
     * @param isRandom     is selection random
     * @return list of filtered rows
     */
    @PostMapping("/inspection/{inspectionId}/rowsFiltered")
    @Transactional
    public JsonNode getRowsFiltered(@PathVariable @NotNull Long inspectionId, @RequestBody Filter filter, @RequestParam("minRange") @NotNull int rangeMin, @RequestParam("maxRange") @NotNull int rangeMax, @RequestParam("isRandom") @NotNull boolean isRandom) throws IOException {
        Inspection inspection = inspectionRepository.getById(inspectionId);
        permissionEvaluator.validateCanReadProject(inspection.getDataset().getProject().getId());

        Table filteredTable = inspectionService.getRowsFiltered(inspectionId, filter);

        if (rangeMax > filteredTable.rowCount()) {
            rangeMax = filteredTable.rowCount();
        }
        if (rangeMin > rangeMax) {
            throw new IllegalArgumentException("minimum range should be less than maximum range");
        }

        Table filteredMTable = isRandom ? filteredTable.sampleN(rangeMax - rangeMin - 1)
            .sortOn(RandomUtils.nextInt(0, 3) - 1) : filteredTable.inRange(rangeMin, rangeMax); //NOSONAR

        ObjectMapper objectMapper = new ObjectMapper();
        String jsonTable = filteredMTable.write().toString("json");
        JsonNode jsonNode = objectMapper.readTree(jsonTable);
        JsonNode result = objectMapper.createObjectNode().set("data", jsonNode);
        ((ObjectNode) result).put("rowNb", filteredTable.rowCount());
        ((ObjectNode) result).set("columns", objectMapper.valueToTree(filteredTable.columnNames()));
        return result;
    }

    @GetMapping("/inspection/{id}")
    public InspectionDTO getInspection(@PathVariable @NotNull Long id) {
        Inspection inspection = inspectionRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.INSPECTION, id));
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
    public InspectionDTO createInspection(@RequestBody @NotNull InspectionCreateDTO createDTO) throws IOException {
        return giskardMapper.toDTO(modelService.createInspection(createDTO.getModelId(), createDTO.getDatasetId()));
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
