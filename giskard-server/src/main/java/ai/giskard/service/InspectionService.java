package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
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
import java.util.List;

import static ai.giskard.web.rest.errors.Entity.INSPECTION;

@Service
@Transactional
@RequiredArgsConstructor
public class InspectionService {

    final UserRepository userRepository;
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final InspectionRepository inspectionRepository;
    final DatasetService datasetService;
    final ApplicationProperties applicationProperties;


    public Table getTableFromBucketFile(String location) throws FileNotFoundException {
        InputStreamReader reader = new InputStreamReader(
            new FileInputStream(location));
        return Table.read().csv(reader);
    }

    private Selection getSelection(Inspection inspection, Filter filter) throws FileNotFoundException {
        Table predsTable = getTableFromBucketFile(inspection.getPredictionsPath().toAbsolutePath().toString());
        Table calculatedTable = getTableFromBucketFile(inspection.getCalculatedPath().toAbsolutePath().toString());
        StringColumn predictedClass = calculatedTable.stringColumn(0);
        StringColumn targetClass = calculatedTable.stringColumn(1);
        Selection correctSelection = predictedClass.isEqualTo(targetClass);
        Selection selection;
        switch (filter.getRowFilter()) {
            case CORRECT:
                selection = correctSelection;
                break;
            case WRONG:
                selection = predictedClass.isNotEqualTo(targetClass);
                break;
            case CUSTOM:
                DoubleColumn probPredicted = (DoubleColumn) predsTable.column(filter.getPredictedLabel());
                Selection predictedSelection = predictedClass.isEqualTo(filter.getPredictedLabel());
                Selection targetSelection = targetClass.isEqualTo(filter.getTargetLabel());
                selection = predictedSelection.and(targetSelection).and(probPredicted.isLessThanOrEqualTo(filter.getMaxThreshold())).and(probPredicted.isGreaterThanOrEqualTo(filter.getMinThreshold()));
                break;
            case BORDERLINE:
                DoubleColumn absDiff = calculatedTable.doubleColumn("absDiff");
                selection = correctSelection.and(absDiff.isLessThanOrEqualTo(applicationProperties.getBorderLineThreshold()));
                break;
            default:
                selection = null;
        }
        return selection;
    }

    /**
     * Get filtered rows
     *
     * @return filtered table
     */
    public Table getRowsFiltered(@NotNull Long inspectionId, @NotNull Filter filter) throws FileNotFoundException {
        Inspection inspection = inspectionRepository.findById(inspectionId).orElseThrow(() -> new EntityNotFoundException(INSPECTION, inspectionId));
        Table table = datasetService.getTableFromDatasetId(inspection.getDataset().getId());
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        Selection selection = getSelection(inspection, filter);
        Table filteredTable = selection == null ? table : table.where(selection);
        return filteredTable;
    }

    /**
     * Get
     *
     * @return filtered table
     */
    public List<String> getLabels(@NotNull Long inspectionId) throws FileNotFoundException {
        Inspection inspection = inspectionRepository.findById(inspectionId).orElseThrow(() -> new EntityNotFoundException(INSPECTION, inspectionId));
        Table predsTable = getTableFromBucketFile(inspection.getPredictionsPath().toAbsolutePath().toString());
        return predsTable.columnNames();
    }

}
