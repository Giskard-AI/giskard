package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.FeatureType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.web.dto.FeatureMetadataDTO;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.univocity.parsers.common.TextParsingException;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tech.tablesaw.api.ColumnType;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;

import javax.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class DatasetService {
    private final Logger log = LoggerFactory.getLogger(DatasetService.class);

    final UserRepository userRepository;
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final InspectionRepository inspectionRepository;
    private final ApplicationProperties applicationProperties;
    private final FileLocationService locationService;
    private final FileUploadService fileUploadService;
    private final PermissionEvaluator permissionEvaluator;

    /**
     *  Read table from file
     *
     * @param datasetId id of the dataset
     * @return the table
     */
    public Table readTableByDatasetId(@NotNull Long datasetId) {
        Dataset dataset = datasetRepository.findById(datasetId).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, datasetId));
        Map<String, ColumnType> columnTypes = dataset.getFeatureTypes().entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> FeatureType.featureToColumn.get(e.getValue())));
        Path filePath = locationService.datasetsDirectory(dataset.getProject().getKey()).resolve(dataset.getFileName());
        String filePathName = filePath.toAbsolutePath().toString().replace(".zst", "");
        Table table;
        try {
            CsvReadOptions csvReadOptions = CsvReadOptions
                .builder(fileUploadService.decompressFileToStream(filePath))
                .columnTypesPartial(columnTypes)
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
    public DatasetDetailsDTO getDetails(@NotNull Long id) {
        Table table = readTableByDatasetId(id);
        DatasetDetailsDTO details = new DatasetDetailsDTO();
        details.setNumberOfRows(table.rowCount());
        details.setColumns(table.columnNames());
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
        Table table = readTableByDatasetId(id);
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        return table.inRange(rangeMin, rangeMax);
    }

    public void deleteDataset(Long datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanWriteProject(dataset.getProject().getId());

        log.info("Deleting dataset from the database: {}", dataset.getId());
        datasetRepository.delete(dataset);

        Path datasetPath = locationService.datasetsDirectory(dataset.getProject().getKey()).resolve(dataset.getFileName());
        try {
            log.info("Removing dataset file: {}", datasetPath.getFileName());
            Files.deleteIfExists(datasetPath);
        } catch (IOException e) {
            throw new RuntimeException(String.format("Failed to remove dataset file %s", datasetPath.getFileName()), e);
        }

    }

    @Transactional
    public List<FeatureMetadataDTO> getFeaturesWithDistinctValues(Long datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanReadProject(dataset.getProject().getId());

        Table data = readTableByDatasetId(datasetId);

        return dataset.getFeatureTypes().entrySet().stream().map(featureAndType -> {
            String featureName = featureAndType.getKey();
            FeatureType type = featureAndType.getValue();
            FeatureMetadataDTO meta = new FeatureMetadataDTO();
            meta.setType(type);
            meta.setName(featureName);
            if (type == FeatureType.CATEGORY) {
                meta.setValues(data.column(featureName).unique().asStringColumn().asSet());
            }
            return meta;

        }).toList();
    }
}
