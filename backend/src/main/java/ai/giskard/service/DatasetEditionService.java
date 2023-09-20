package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.utils.CsvEditStream;
import ai.giskard.web.rest.errors.BadRequestException;
import jakarta.transaction.Transactional;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.apache.commons.csv.CSVRecord;
import org.apache.commons.lang3.NotImplementedException;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

@Service
@RequiredArgsConstructor
@Transactional
public class DatasetEditionService {
    public static final String GISKARD_DATASET_UID_COLUMN = "__GSK_UID__";

    private final DatasetRepository datasetRepository;
    private final FileLocationService locationService;

    private void ensureEditable(Dataset dataset) {
        if (!dataset.isEditable()) {
            throw new BadRequestException("Readonly dataset");
        }
    }

    public Dataset addRow(UUID datasetId, Map<@NotNull String, @NotNull String> row) {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        ensureEditable(dataset);

        throw new NotImplementedException("This feature is not available ATM");

    }

    public Dataset deleteRow(UUID datasetId, int rowId) throws IOException {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        ensureEditable(dataset);

        deleteDatasetRow(dataset, rowId, true);
        int totalRows = deleteDatasetRow(dataset, rowId, false);

        for (Inspection inspection : dataset.getInspections()) {
            deletePredictionRow(inspection, rowId);
        }

        // TODO: update file size
        dataset.setNumberOfRows(totalRows);
        datasetRepository.save(dataset);

        return dataset;
    }

    private int deleteDatasetRow(Dataset dataset, int rowId, boolean sample) throws IOException {
        String rowIdStr = String.valueOf(rowId);
        return deleteCsvRow(locationService.resolvedDatasetCsvPath(dataset, sample), true,
            record -> record.get(GISKARD_DATASET_UID_COLUMN).equals(rowIdStr));
    }

    private void deletePredictionRow(Inspection inspection, int rowId) throws IOException {
        // TODO fix row retrieval
        deleteCsvRowIfExists(rowId, locationService.resolvedInspectionPredictionsPath(inspection, true), false);
        deleteCsvRowIfExists(rowId, locationService.resolvedInspectionPredictionsPath(inspection, false), false);
        deleteCsvRowIfExists(rowId, locationService.resolvedInspectionCalculatedPath(inspection, true), false);
        deleteCsvRowIfExists(rowId, locationService.resolvedInspectionCalculatedPath(inspection, false), false);
    }

    private void deleteCsvRowIfExists(int rowId, Path path, boolean compressed) throws IOException {
        if (Files.exists(path)) {
            String rowIdStr = String.valueOf(rowId);
            deleteCsvRow(path, compressed, record -> record.get(GISKARD_DATASET_UID_COLUMN).equals(rowIdStr));
        }
    }

    private int deleteCsvRow(Path path, boolean compressed, Predicate<CSVRecord> shouldKeepRow) throws IOException {
        int rows = 0;
        try (CsvEditStream csvEditStream = new CsvEditStream(path, compressed)) {
            for (Iterator<CSVRecord> it = csvEditStream.iterator(); it.hasNext(); ) {
                CSVRecord record = it.next();

                if (shouldKeepRow.test(record)) {
                    csvEditStream.write(record);
                    rows++;
                }
            }
        }

        return rows;
    }

    private int deleteCsvRow(Path path, boolean compressed, Predicate<CSVRecord> shouldKeepRow) throws IOException {
        int rows = 0;
        try (CsvEditStream csvEditStream = new CsvEditStream(path, compressed)) {
            for (Iterator<CSVRecord> it = csvEditStream.iterator(); it.hasNext(); ) {
                CSVRecord record = it.next();

                if (shouldKeepRow.test(record)) {
                    csvEditStream.write(record);
                    rows++;
                }
            }
        }

        return rows;
    }

}
