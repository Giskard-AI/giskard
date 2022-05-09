package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.table.Filter;
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
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.selection.Selection;

import javax.validation.constraints.NotNull;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStreamReader;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.stream.Collectors;

import static ai.giskard.domain.ml.table.TableConstants.BORDERLINE_THRESHOLD;

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

    public Table getTableFromBucketFile(String location) throws FileNotFoundException {
        InputStreamReader reader = new InputStreamReader(
            new FileInputStream(location));
        return Table.read().csv(reader);
    }

    public Table getPredsTable(@NotNull Long datasetId, @NotNull Long modelId) throws FileNotFoundException {
        Path filePath = Paths.get(applicationProperties.getBucketPath(), "files-bucket", "inspections", String.format("%s_%s", modelId, datasetId), "predictions.csv");
        return getTableFromBucketFile(filePath.toAbsolutePath().toString());
    }

    public Table getCalculatedTable(@NotNull Long datasetId, @NotNull Long modelId) throws FileNotFoundException {
        Path filePath = Paths.get(applicationProperties.getBucketPath(), "files-bucket", "inspections", String.format("%s_%s", modelId, datasetId), "calculated.csv");
        return getTableFromBucketFile(filePath.toAbsolutePath().toString());
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

    private Selection getSelection(Table table, Long datasetId, Long modelId, Filter filter) throws FileNotFoundException {
        Table predsTable = getPredsTable(datasetId, modelId);
        Table predsNoTargetTable= predsTable.rejectColumns(filter.getTarget());
        Table calculatedTable = getCalculatedTable(datasetId, modelId);
        StringColumn predictedClass=calculatedTable.stringColumn(0);
        DoubleColumn probTarget = (DoubleColumn) predsTable.column( filter.getTarget());
        Selection correctSelection=predictedClass.lowerCase().isEqualTo(filter.getTarget().toLowerCase());
        Selection selection;
        switch (filter.getRowFilter()) {
            case CORRECT:
                selection=correctSelection;
                break;
            case WRONG:
                selection=predictedClass.lowerCase().isNotEqualTo(filter.getTarget().toLowerCase());
                break;
            case CUSTOM:
                selection = correctSelection.and(probTarget.isLessThanOrEqualTo(filter.getMaxThreshold()));
                break;
            case BORDERLINE:
                DoubleColumn _max = DoubleColumn.create("max", predsNoTargetTable.stream().mapToDouble(row -> Collections.max(row.columnNames().stream().map(name -> row.getDouble(name)).collect(Collectors.toList()))));
                DoubleColumn absDiff=_max.subtract(probTarget).abs();
                // TODO Check if correct filter needed
                selection=predictedClass.lowerCase().isEqualTo(filter.getTarget().toLowerCase());
                selection=selection.and(absDiff.isLessThanOrEqualTo(BORDERLINE_THRESHOLD));
                break;
            default:
                selection = null;
        }
        return selection;
    }

    /**
     * Get filtered rows
     *
     * @param datasetId dataset id
     * @return filtered table
     */
    public Table getRowsFiltered(@NotNull Long datasetId, @NotNull Long modelId, @NotNull Filter filter) throws FileNotFoundException {
        Table table = getTableFromDatasetId(datasetId);
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        Selection selection = getSelection(table, datasetId, modelId, filter);
        Table filteredTable = selection == null ? table : table.where(selection);
        return filteredTable;
    }
}
