package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.service.DatasetService;
import ai.giskard.service.InspectionService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.json.JsonWriter;

import javax.validation.constraints.NotNull;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class InspectionController {

    private final InspectionService inspectionService;

    /**
     * Retrieve the row specified by the given range on the dataset
     * TODO Replace with spring pagination
     *
     * @param inspectionId id of the inspection
     * @return List of rows
     */
    @PostMapping("/inspection/{inspectionId}/rowsFiltered")
    public JsonNode getRowsFiltered(@PathVariable @NotNull Long inspectionId, @RequestBody Filter filter, @RequestParam("minRange") @NotNull int rangeMin, @RequestParam("maxRange") @NotNull int rangeMax) throws Exception {
        Table filteredTable = inspectionService.getRowsFiltered(inspectionId, filter);
        if (rangeMin >= rangeMax || rangeMin >= filteredTable.rowCount()) {
            throw new Exception("range are not correct for the results");//TODO Precise exception
        }
        rangeMax = Math.min(rangeMax, filteredTable.rowCount());
        Table filteredMTable = filteredTable.inRange(rangeMin, rangeMax);
        ObjectMapper objectMapper = new ObjectMapper();
        String jsonTable = filteredMTable.write().toString("json");
        JsonNode jsonNode = objectMapper.readTree(jsonTable);
        JsonNode result = objectMapper.createObjectNode().set("data", jsonNode);
        ((ObjectNode) result).put("rowNb", filteredTable.rowCount());
        ((ObjectNode) result).set("columns", objectMapper.valueToTree(filteredTable.columnNames()));
        return result;
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
