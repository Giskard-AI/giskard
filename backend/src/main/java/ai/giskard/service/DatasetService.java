package ai.giskard.service;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.utils.FileUtils;
import ai.giskard.utils.StreamUtils;
import ai.giskard.web.dto.DatasetPageDTO;
import ai.giskard.web.dto.RowFilterDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.univocity.parsers.common.TextParsingException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;

import jakarta.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.UUID;
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
     * @param sample    whenever only reading the sample file or not
     * @return the table
     */
    public Table readTableByDatasetId(@NotNull UUID datasetId, boolean sample) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        Map<String, tech.tablesaw.api.ColumnType> columnDtypes = dataset.getColumnTypes().entrySet().stream()
            .collect(Collectors.toMap(Map.Entry::getKey, e -> ColumnType.featureToColumn.get(e.getValue())));

        Path filePath = getDataFile(dataset, sample);

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

    private Path getDataFile(@NotNull Dataset dataset, boolean sample) {
        return locationService.datasetsDirectory(dataset.getProject().getKey())
            .resolve(dataset.getId().toString())
            .resolve(FileUtils.getFileName("data", "csv.zst", sample));
    }

    /**
     * Get filtered rows
     *
     * @param id       dataset id
     * @param rangeMin min range of the dataset
     * @param rangeMax max range of the dataset
     * @return filtered table
     */
    public DatasetPageDTO getRows(@NotNull UUID id, @NotNull int rangeMin, @NotNull int rangeMax,
                                  RowFilterDTO rowFilter, boolean sample) throws IOException {
        Table table = readTableByDatasetId(id, sample);
        IntColumn indexColumn = IntColumn.indexColumn(GISKARD_DATASET_INDEX_COLUMN_NAME, table.rowCount(), 0);
        table.addColumns(indexColumn);

        if (rowFilter.getFilter() != null) {
            table = inspectionService.getRowsFiltered(table, rowFilter.getFilter());
        }

        if (rowFilter.getRemoveRows() != null) {
            table = table.where(table.intColumn(GISKARD_DATASET_INDEX_COLUMN_NAME).isNotIn(rowFilter.getRemoveRows()));
        }

        return new DatasetPageDTO(table.rowCount(), table.inRange(rangeMin, Math.min(table.rowCount(), rangeMax)).stream()
            .map(row -> row.columnNames().stream()
                .collect(StreamUtils.toMapAllowNulls(Function.identity(), row::getObject)))
            .toList());
    }

    public Dataset renameDataset(UUID datasetId, String name) {
        Dataset dataset = datasetRepository.findById(datasetId)
            .orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, datasetId.toString()));

        permissionEvaluator.validateCanWriteProject(dataset.getProject().getId());

        dataset.setName(name);

        return datasetRepository.save(dataset);
    }
}
