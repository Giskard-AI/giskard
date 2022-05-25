package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.service.DatasetService;
import ai.giskard.service.InspectionService;
import ai.giskard.service.ModelService;
import ai.giskard.web.dto.InspectionCreateDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.InspectionDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.RandomUtils;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Row;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.io.FileNotFoundException;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class InspectionController {

    private final InspectionService inspectionService;
    private final ModelService modelService;
    private final InspectionRepository inspectionRepository;
    private final DatasetService datasetService;
    private final GiskardMapper giskardMapper;

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
     * @throws Exception
     */
    @PostMapping("/inspection/{inspectionId}/rowsFiltered")
    public JsonNode getRowsFiltered(@PathVariable @NotNull Long inspectionId, @RequestBody Filter filter, @RequestParam("minRange") @NotNull int rangeMin, @RequestParam("maxRange") @NotNull int rangeMax, @RequestParam("isRandom") @NotNull boolean isRandom) throws Exception {
        Table filteredTable = inspectionService.getRowsFiltered(inspectionId, filter);
        if (rangeMax > filteredTable.rowCount()) {
            rangeMax = filteredTable.rowCount();
        }
        if (rangeMin > rangeMax) {
            throw new IllegalArgumentException("minumum range shoud be less than maximum range");
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
    public List<String> getLabels(@PathVariable @NotNull Long inspectionId) throws JsonProcessingException {
        return inspectionService.getLabels(inspectionId);
    }

    @PostMapping("/inspection")
    public InspectionDTO createInspection(@RequestBody @NotNull InspectionCreateDTO createDTO) {
        return giskardMapper.toDTO(modelService.createInspection(createDTO.getModelId(), createDTO.getDatasetId()));
    }


}
