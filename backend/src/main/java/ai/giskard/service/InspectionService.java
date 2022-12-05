package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.table.Filter;
import ai.giskard.repository.InspectionRepository;
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

import static ai.giskard.domain.ml.table.RowFilterType.CUSTOM;
import static ai.giskard.service.DatasetService.GISKARD_DATASET_INDEX_COLUMN_NAME;
import static ai.giskard.web.rest.errors.Entity.INSPECTION;

@Service
@Transactional
@RequiredArgsConstructor
public class InspectionService {

    private final InspectionRepository inspectionRepository;
    private final DatasetService datasetService;
    private final ApplicationProperties applicationProperties;
    private final FileLocationService fileLocationService;

    public Table getTableFromBucketFile(String location) throws FileNotFoundException {
        InputStreamReader reader = new InputStreamReader(new FileInputStream(location));
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

    /**
     * Returns regression selection given filter parameters
     * TODO: Refactor this
     *
     * @param inspection inspection
     * @param filter     filter parameters
     * @return selection
     * @throws FileNotFoundException when file not found
     */
    private Selection getSelectionRegression(Inspection inspection, Filter filter) throws FileNotFoundException {
        Table calculatedTable = getTableFromBucketFile(getCalculatedPath(inspection).toString());
        Selection selection = null;
        Double threshold;
        if (inspection.getDataset().getTarget() != null) {
            DoubleColumn absDiffPercentColumn = calculatedTable.doubleColumn("absDiffPercent");
            DoubleColumn diffPercent = calculatedTable.doubleColumn("diffPercent");
            switch (filter.getType()) {
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
                        selection = selection.and(diffPercent.isLessThanOrEqualTo(filter.getMaxDiffThreshold() / 100));
                    }
                    if (filter.getMinDiffThreshold() != null) {
                        selection = selection.and(diffPercent.isGreaterThanOrEqualTo(filter.getMinDiffThreshold() / 100));
                    }
                }
                default -> {
                }
            }
        } else if (filter.getType() == CUSTOM) {
            DoubleColumn prediction = calculatedTable.doubleColumn(0);
            selection = prediction.isNotMissing();
            if (filter.getMinThreshold() != null) {
                selection = selection.and(prediction.isGreaterThanOrEqualTo(filter.getMinThreshold()));
            }
            if (filter.getMaxThreshold() != null) {
                selection = selection.and(prediction.isLessThanOrEqualTo(filter.getMaxThreshold()));
            }
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
        Selection selection = predictedClass.isNotMissing();
        if (inspection.getDataset().getTarget() != null) {
            StringColumn targetClass = calculatedTable.stringColumn(1);
            Selection correctSelection = predictedClass.isEqualTo(targetClass);
            switch (filter.getType()) {
                case CORRECT -> selection = correctSelection;
                case WRONG -> selection = predictedClass.isNotEqualTo(targetClass);
                case CUSTOM -> {
                    if (filter.getTargetLabel().length > 0) {
                        selection.and(targetClass.isIn(filter.getTargetLabel()));
                    }
                    customClassifFilters(filter, predsTable, predictedClass, selection);
                }
                case BORDERLINE -> {
                    DoubleColumn absDiff = calculatedTable.doubleColumn("absDiff");
                    selection = correctSelection.and(absDiff.isLessThanOrEqualTo(applicationProperties.getBorderLineThreshold()));
                }
                default -> selection = null;
            }
        } else if (filter.getType() == CUSTOM) {
            customClassifFilters(filter, predsTable, predictedClass, selection);
        }
        return selection;
    }

    private void customClassifFilters(Filter filter, Table predsTable, StringColumn predictedClass, Selection selection) {
        if (filter.getPredictedLabel().length > 0) {
            selection.and(predictedClass.isIn(filter.getPredictedLabel()));
        }
        if (filter.getThresholdLabel() != null) {
            DoubleColumn probPredicted = (DoubleColumn) predsTable.column(filter.getThresholdLabel());
            if (filter.getMaxThreshold() != null) {
                selection.and(probPredicted.isLessThanOrEqualTo(filter.getMaxThreshold() / 100));
            }
            if (filter.getMinThreshold() != null) {
                selection.and(probPredicted.isGreaterThanOrEqualTo(filter.getMinThreshold() / 100));
            }
        }
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
        table.addColumns(IntColumn.indexColumn(GISKARD_DATASET_INDEX_COLUMN_NAME, table.rowCount(), 0));
        Selection selection = inspection.getModel().getModelType().isClassification() ? getSelection(inspection, filter) : getSelectionRegression(inspection, filter);
        return selection == null ? table : table.where(selection);
    }

    /**
     * Get labels
     *
     * @return filtered table
     */
    @Transactional
    public List<String> getLabels(@NotNull Long inspectionId) {
        Inspection inspection = inspectionRepository.getById(inspectionId);
        return inspection.getModel().getClassificationLabels();
    }


}
