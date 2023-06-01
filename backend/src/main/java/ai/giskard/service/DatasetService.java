package ai.giskard.service;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.utils.StreamUtils;
import ai.giskard.web.dto.DatasetMetadataDTO;
import ai.giskard.web.dto.DatasetPageDTO;
import ai.giskard.web.dto.FeatureMetadataDTO;
import ai.giskard.web.dto.RowFilterDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.univocity.parsers.common.TextParsingException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class DatasetService {
    public static final String GISKARD_DATASET_INDEX_COLUMN_NAME = "_GISKARD_INDEX_";

    private final DatasetRepository datasetRepository;
    private final FileLocationService locationService;
    private final FileUploadService fileUploadService;
    private final PermissionEvaluator permissionEvaluator;
    private final InspectionService inspectionService;

    /**
     * Read table from file
     *
     * @param datasetId id of the dataset
     * @return the table
     */
    public Table readTableByDatasetId(@NotNull UUID datasetId) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        Map<String, tech.tablesaw.api.ColumnType> columnDtypes = dataset.getColumnTypes().entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> ColumnType.featureToColumn.get(e.getValue())));
        Path filePath = locationService.datasetsDirectory(dataset.getProject().getKey())
            .resolve(dataset.getId().toString()).resolve("data.csv.zst");
        String filePathName = filePath.toAbsolutePath().toString().replace(".zst", "");
        Table table;
        try {
            CsvReadOptions csvReadOptions = CsvReadOptions
                .builder(fileUploadService.decompressFileToStream(filePath))
                .columnTypesPartial(columnDtypes)
                .missingValueIndicator("_GSK_NA_")
                .maxCharsPerColumn(-1)
                .build();
            table = Table.read().csv(csvReadOptions);
        } catch (TextParsingException e) {
            CsvReadOptions options = CsvReadOptions.builder(filePathName).maxCharsPerColumn(2000000).build();
            table = Table.read().csv(options);
        }
        return table;
    }

    /**
     * Get details of dataset
     *
     * @param id dataset's id
     * @return details dto of the dataset
     */
    public DatasetDetailsDTO getDetails(@NotNull UUID id) {
        Table table = readTableByDatasetId(id);
        DatasetDetailsDTO details = new DatasetDetailsDTO();
        details.setNumberOfRows(table.rowCount());
        details.setColumns(table.columnNames());
        return details;
    }

    public DatasetMetadataDTO getMetadata(@NotNull UUID id) {
        Dataset dataset = this.datasetRepository.getMandatoryById(id);
        DatasetMetadataDTO metadata = new DatasetMetadataDTO();
        metadata.setId(id);
        metadata.setColumnDtypes(dataset.getColumnDtypes());
        metadata.setTarget(dataset.getTarget());
        metadata.setColumnTypes(dataset.getColumnTypes());
        return metadata;
    }

    /**
     * Get filtered rows
     *
     * @param id       dataset id
     * @param rangeMin min range of the dataset
     * @param rangeMax max range of the dataset
     * @return filtered table
     */
    public DatasetPageDTO getRows(@NotNull UUID id, @NotNull int rangeMin, @NotNull int rangeMax, RowFilterDTO rowFilter) throws IOException {
        Table table = readTableByDatasetId(id);
        table.addColumns(IntColumn.indexColumn(GISKARD_DATASET_INDEX_COLUMN_NAME, table.rowCount(), 0));

        if (rowFilter.getFilter() != null) {
            table = inspectionService.getRowsFiltered(table, rowFilter.getFilter());
        }

        if (rowFilter.getRemoveRows() != null) {
            Table finalTable = table;
            table = table.dropRows(Arrays.stream(rowFilter.getRemoveRows())
                .mapToObj(idx -> finalTable.stream().filter(row -> row.getInt(GISKARD_DATASET_INDEX_COLUMN_NAME) == idx).findFirst())
                .filter(Optional::isPresent)
                .mapToInt(row -> row.get().getRowNumber())
                .toArray());
        }

        return new DatasetPageDTO(table.rowCount(), table.inRange(rangeMin, Math.min(table.rowCount(), rangeMax)).stream()
            .map(row -> row.columnNames().stream()
                .collect(StreamUtils.toMapAllowNulls(Function.identity(), row::getObject)))
            .toList());
    }

    public List<FeatureMetadataDTO> getFeaturesWithDistinctValues(UUID datasetId) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        permissionEvaluator.validateCanReadProject(dataset.getProject().getId());

        Table data = readTableByDatasetId(datasetId);

        return dataset.getColumnTypes().entrySet().stream().map(featureAndType -> {
            String featureName = featureAndType.getKey();
            ColumnType type = featureAndType.getValue();
            FeatureMetadataDTO meta = new FeatureMetadataDTO();
            meta.setType(type);
            meta.setName(featureName);
            if (type == ColumnType.CATEGORY) {
                meta.setValues(data.column(featureName).unique().asStringColumn().asSet());
            }
            return meta;

        }).toList();
    }

    public Dataset renameDataset(UUID datasetId, String name) {
        Dataset dataset = datasetRepository.findById(datasetId)
            .orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, datasetId.toString()));

        permissionEvaluator.validateCanWriteProject(dataset.getProject().getId());

        dataset.setName(name);

        return datasetRepository.save(dataset);
    }
}
