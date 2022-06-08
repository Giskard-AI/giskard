package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tech.tablesaw.api.*;
import tech.tablesaw.io.csv.CsvReadOptions;
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

    public Table getTableFromBucketFile(String location, ColumnType[] columnTypes) throws FileNotFoundException {
        InputStreamReader reader = new InputStreamReader(
            new FileInputStream(location));
        CsvReadOptions csvReadOptions = CsvReadOptions
            .builder(reader)
            .columnTypes(columnTypes)
            .build();
        return Table.read().csv(csvReadOptions);
    }

    private Double getThresholdForRegression(DoubleColumn predColumn, boolean isCorrect) {
        DoubleColumn column = predColumn.copy();
        if (isCorrect) {
            column.sortAscending();
        } else {
            column.sortDescending();
        }
        int maxIndex = (int) Math.round(applicationProperties.getRegressionThreshold() * column.size());
        return column.get(maxIndex);
    }

    private Selection getSelectionRegression(Inspection inspection, Filter filter) throws FileNotFoundException {
        Table calculatedTable = getTableFromBucketFile(getCalculatedPath(inspection).toString());
        Selection selection;
        Double threshold;
        DoubleColumn absDiffPercentColumn = calculatedTable.doubleColumn("absDiffPercent");
        DoubleColumn diffPercent = calculatedTable.doubleColumn("diffPercent");
        switch (filter.getRowFilter()) {
            case CORRECT -> {
                threshold = getThresholdForRegression(absDiffPercentColumn, true);
                selection = absDiffPercentColumn.isLessThanOrEqualTo(threshold);
            }
            case WRONG -> {
                threshold = getThresholdForRegression(absDiffPercentColumn, false);
                selection = absDiffPercentColumn.isGreaterThanOrEqualTo(threshold);
            }
            case CUSTOM -> {
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
                if (filter.getMaxDiffThreshold() != null) {
                    selection = selection.and(diffPercent.isLessThanOrEqualTo(filter.getMaxDiffThreshold()));
                }
                if (filter.getMinDiffThreshold() != null) {
                    selection = selection.and(diffPercent.isGreaterThanOrEqualTo(filter.getMinDiffThreshold()));
                }
            }
            default -> selection = null;
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
        ColumnType[] columnTypes = {ColumnType.STRING, ColumnType.STRING, ColumnType.DOUBLE};
        Table calculatedTable = getTableFromBucketFile(getCalculatedPath(inspection).toString(), columnTypes);
        StringColumn predictedClass = calculatedTable.stringColumn(0);
        StringColumn targetClass = calculatedTable.stringColumn(1);
        Selection correctSelection = predictedClass.isEqualTo(targetClass);
        Selection selection;
        switch (filter.getRowFilter()) {
            case CORRECT -> selection = correctSelection;
            case WRONG -> selection = predictedClass.isNotEqualTo(targetClass);
            case CUSTOM -> {
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
            }
            case BORDERLINE -> {
                DoubleColumn absDiff = calculatedTable.doubleColumn("absDiff");
                selection = correctSelection.and(absDiff.isLessThanOrEqualTo(applicationProperties.getBorderLineThreshold()));
            }
            default -> selection = null;
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
        return selection == null ? table : table.where(selection);
    }

    /**
     * Get
     *
     * @return filtered table
     */
    @Transactional
    public List<String> getLabels(@NotNull Long inspectionId) {
        Inspection inspection = inspectionRepository.getById(inspectionId);
        return inspection.getModel().getClassificationLabels();
    }


}
