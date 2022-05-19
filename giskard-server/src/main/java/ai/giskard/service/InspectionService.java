package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.web.dto.mapper.SimpleJSONMapper;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.core.JsonProcessingException;
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
    final PermissionEvaluator permissionEvaluator;
    final FileLocationService fileLocationService;

    public Table getTableFromBucketFile(String location) throws FileNotFoundException {
        InputStreamReader reader = new InputStreamReader(
            new FileInputStream(location));
        return Table.read().csv(reader);
    }

    private Double getThresholdForRegression(DoubleColumn _column) {
        DoubleColumn column = _column.copy();
        column.sortAscending();
        int maxIndex = (int) Math.round(applicationProperties.getRegressionThreshold() * column.size());
        return column.get(maxIndex);
    }

    private Selection getSelectionRegression(Inspection inspection, Filter filter) throws FileNotFoundException {
        Table calculatedTable = getTableFromBucketFile(getCalculatedPath(inspection).toString());
        Selection selection;
        Double threshold;
        DoubleColumn column = calculatedTable.doubleColumn("absDiffPercent");
        switch (filter.getRowFilter()) {
            case CORRECT:
                threshold = getThresholdForRegression(column);
                selection = column.isLessThanOrEqualTo(threshold);
                break;
            case WRONG:
                threshold = getThresholdForRegression(column);
                selection = column.isGreaterThanOrEqualTo(threshold);
                break;
            case CUSTOM:
                DoubleColumn prediction = calculatedTable.doubleColumn(0);
                DoubleColumn target = calculatedTable.numberColumn(1).asDoubleColumn();
                selection = prediction.isNotMissing();
                if (filter.getMinThreshold() != null) {
                    selection = selection.and(prediction.isGreaterThanOrEqualTo(filter.getMinThreshold()));
                }
                if (filter.getMaxThreshold() != null) {
                    selection = selection.and(prediction.isLessThanOrEqualTo(filter.getMaxThreshold()));
                }
                if (filter.getMinLabelThreshold() != null) {
                    selection = selection.and(target.isGreaterThanOrEqualTo(filter.getMinLabelThreshold()));
                }
                if (filter.getMaxLabelThreshold() != null) {
                    selection = selection.and(target.isLessThanOrEqualTo(filter.getMaxLabelThreshold()));
                }
                break;
            default:
                selection = null;
        }
        return selection;
    }

    public Path getPredictionsPath(Inspection inspection) {
        String projectKey = inspection.getModel().getProject().getKey();
        return fileLocationService.resolvedInspectionPath(projectKey, inspection.getId()).resolve("predictions.csv");
    }

    public Path getCalculatedPath(Inspection inspection) {
        String projectKey = inspection.getModel().getProject().getKey();
        return fileLocationService.resolvedInspectionPath(projectKey, inspection.getId()).resolve("calculated.csv");
    }

    private Selection getSelection(Inspection inspection, Filter filter) throws FileNotFoundException {
        Table predsTable = getTableFromBucketFile(getPredictionsPath(inspection).toString());
        Table calculatedTable = getTableFromBucketFile(getCalculatedPath(inspection).toString());
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
                DoubleColumn probPredicted = (DoubleColumn) predsTable.column(filter.getThresholdLabel());
                selection = targetClass.isNotMissing();
                if (filter.getPredictedLabel().length > 0) {
                    selection.and(predictedClass.isIn(filter.getPredictedLabel()));
                }
                if (filter.getTargetLabel().length > 0) {
                    selection.and(targetClass.isIn(filter.getTargetLabel()));
                }
                if (filter.getMaxThreshold() != null) {
                    selection.and(probPredicted.isLessThanOrEqualTo(filter.getMaxThreshold()));
                }
                if (filter.getMinThreshold() != null) {
                    selection.and(probPredicted.isGreaterThanOrEqualTo(filter.getMinThreshold()));
                }
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
    @Transactional
    public Table getRowsFiltered(@NotNull Long inspectionId, @NotNull Filter filter) throws FileNotFoundException {
        Inspection inspection = inspectionRepository.findById(inspectionId).orElseThrow(() -> new EntityNotFoundException(INSPECTION, inspectionId));
        Table table = datasetService.readTableByDatasetId(inspection.getDataset().getId());
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        Selection selection = inspection.getModel().getModelType().isClassification() ? getSelection(inspection, filter) : getSelectionRegression(inspection, filter);
        Table filteredTable = selection == null ? table : table.where(selection);
        return filteredTable;
    }

    /**
     * Get
     *
     * @return filtered table
     */
    @Transactional
    public List<String> getLabels(@NotNull Long inspectionId) throws JsonProcessingException {
        Inspection inspection = inspectionRepository.getById(inspectionId);
        return SimpleJSONMapper.toListOfStrings(inspection.getModel().getClassificationLabels());
    }


}
