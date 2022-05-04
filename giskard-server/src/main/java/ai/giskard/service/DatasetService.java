package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.RowFilter;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tech.tablesaw.api.DoubleColumn;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.selection.Selection;

import javax.validation.constraints.NotNull;
import java.nio.file.Path;
import java.nio.file.Paths;

@Service
@Transactional
@RequiredArgsConstructor
public class DatasetService {

    final UserRepository userRepository;
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    private final ApplicationProperties applicationProperties;

    public Table getTableFromDatasetId(@NotNull Long id) {
        Dataset dataset = datasetRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, id));
        Path filePath = Paths.get(applicationProperties.getBucketPath(), dataset.getLocation());
        String filePathName = filePath.toAbsolutePath().toString().replace(".zst", "");
        return Table.read().csv(filePathName);
    }

    public Table getProbsTableFromModelId(@NotNull Long datasetId, @NotNull Long modelId) {
        Path filePath = Paths.get(applicationProperties.getBucketPath(), "files-bucket", String.format("%s_%s.csv", modelId, datasetId));
        return Table.read().csv(filePath.toAbsolutePath().toString());
    }

    /**
     * Get details of dataset
     *
     * @param id dataset's id
     * @return details dto of the dataset
     */
    public DatasetDetailsDTO getDetails(@NotNull Long id) {
        Table table = getTableFromDatasetId(id);
        DatasetDetailsDTO details = new DatasetDetailsDTO();
        details.setNumberOfRows(table.rowCount());
        return details;
    }

    /**
     * Get filtered rows
     *
     * @param id       dataset id
     * @param rangeMin min range of the dataset
     * @param rangeMax max range of the dataset
     * @return filtered table
     */
    public Table getRows(@NotNull Long id, @NotNull int rangeMin, @NotNull int rangeMax) {
        Table table = getTableFromDatasetId(id);
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        Table filteredTable = table.inRange(rangeMin, rangeMax);
        return filteredTable;
    }

    /**
     * Get filtered rows
     *
     * @param datasetId dataset id
     * @return filtered table
     */
    public Table getRowsFiltered(@NotNull Long datasetId, @NotNull Long modelId, @NotNull String target, @NotNull float threshold, @NotNull RowFilter rowFilter) {
        Table table = getTableFromDatasetId(datasetId);
        Table probsTable = getProbsTableFromModelId(datasetId, modelId);
        //Table result = table.append(probsTable);
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        DoubleColumn probTarget = (DoubleColumn) probsTable.column("predictions_" + target);
        Selection selection = null;
        IntColumn labelColumn= (IntColumn) table.column(target.toLowerCase());
        DoubleColumn finalColumn= labelColumn.multiply(probTarget);
        if (rowFilter == RowFilter.GREATER) {
            selection = finalColumn.isGreaterThan(threshold);
        } else if (rowFilter == RowFilter.LOWER) {
            selection = finalColumn.isLessThan(threshold);
        }
        Table filteredTable = selection == null ?  table: table.where(selection);
        return filteredTable;
    }
}
