package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.service.InspectionService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.InspectionDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Row;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.io.FileNotFoundException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class InspectionController {

    private final InspectionService inspectionService;
    private final InspectionRepository inspectionRepository;
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
        List<Integer> ranges = Arrays.asList(rangeMin, rangeMax, filteredTable.rowCount());
        Collections.sort(ranges);
        Table filteredMTable = isRandom ? filteredTable.sampleN(ranges.get(1) - ranges.get(0) - 1).sortOn((Row o1, Row o2) -> Math.random() > 0.5 ? -1 : 1) : filteredTable.inRange(ranges.get(0), ranges.get(1));
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
        return giskardMapper.inspectionToInspectionDTO(inspection);
    }


    /**
     * get the labels for the target column
     *
     * @param inspectionId id of the inspection
     * @return List of labels
     */
    @GetMapping("/inspection/{inspectionId}/labels")
    public List<String> getLabels(@PathVariable @NotNull Long inspectionId) throws FileNotFoundException {
        return inspectionService.getLabels(inspectionId);
    }


}
