package ai.giskard.service;

import ai.giskard.domain.ColumnMeaning;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.web.dto.DatasetMetadataDTO;
import ai.giskard.web.dto.FeatureMetadataDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.univocity.parsers.common.TextParsingException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tech.tablesaw.api.ColumnType;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;

import javax.validation.constraints.NotNull;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class DatasetService {
    public static final String GISKARD_DATASET_INDEX_COLUMN_NAME = "_GISKARD_INDEX_";

    private final DatasetRepository datasetRepository;
    private final FileLocationService locationService;
    private final FileUploadService fileUploadService;
    private final PermissionEvaluator permissionEvaluator;

    /**
     * Read table from file
     *
     * @param datasetId id of the dataset
     * @return the table
     */
    public Table readTableByDatasetId(@NotNull UUID datasetId) {
        Dataset dataset = datasetRepository.findById(datasetId).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, datasetId.toString()));
        Map<String, ColumnType> columnTypes = dataset.getColumnMeanings().entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> ColumnMeaning.featureToColumn.get(e.getValue())));
        Path filePath = locationService.datasetsDirectory(dataset.getProject().getKey())
            .resolve(dataset.getId().toString()).resolve("data.csv.zst");
        String filePathName = filePath.toAbsolutePath().toString().replace(".zst", "");
        Table table;
        try {
            CsvReadOptions csvReadOptions = CsvReadOptions
                .builder(fileUploadService.decompressFileToStream(filePath))
                .columnTypesPartial(columnTypes)
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
        Dataset dataset = this.datasetRepository.getById(id);
        DatasetMetadataDTO metadata = new DatasetMetadataDTO();
        metadata.setId(id);
        metadata.setColumnTypes(dataset.getColumnTypes());
        metadata.setTarget(dataset.getTarget());
        metadata.setColumnMeanings(dataset.getColumnMeanings());
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
    public Table getRows(@NotNull UUID id, @NotNull int rangeMin, @NotNull int rangeMax) {
        Table table = readTableByDatasetId(id);
        table.addColumns(IntColumn.indexColumn(GISKARD_DATASET_INDEX_COLUMN_NAME, table.rowCount(), 0));
        return table.inRange(rangeMin, rangeMax);
    }

    @Transactional
    public List<FeatureMetadataDTO> getFeaturesWithDistinctValues(UUID datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanReadProject(dataset.getProject().getId());

        Table data = readTableByDatasetId(datasetId);

        return dataset.getColumnMeanings().entrySet().stream().map(featureAndType -> {
            String featureName = featureAndType.getKey();
            ColumnMeaning type = featureAndType.getValue();
            FeatureMetadataDTO meta = new FeatureMetadataDTO();
            meta.setType(type);
            meta.setName(featureName);
            if (type == ColumnMeaning.CATEGORY) {
                meta.setValues(data.column(featureName).unique().asStringColumn().asSet());
            }
            return meta;

        }).toList();
    }

}
