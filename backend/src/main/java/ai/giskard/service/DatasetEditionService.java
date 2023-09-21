package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.web.rest.errors.BadRequestException;
import com.github.luben.zstd.ZstdInputStream;
import com.github.luben.zstd.ZstdOutputStream;
import jakarta.transaction.Transactional;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.csv.CSVRecord;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Predicate;

@Service
@RequiredArgsConstructor
@Transactional
public class DatasetEditionService {

    private static final String GISKARD_DATASET_UID_COLUMN = "__GSK_UID__";
    private static final CSVFormat READER_FORMAT = CSVFormat.DEFAULT.builder()
        .setHeader()
        .setSkipHeaderRecord(true)
        .build();
    private static final CSVFormat WRITER_FORMAT = CSVFormat.DEFAULT.builder()
        .setHeader()
        .setSkipHeaderRecord(false)
        .build();

    private final DatasetRepository datasetRepository;
    private final FileLocationService locationService;

    private void ensureEditable(Dataset dataset) {
        if (!dataset.isEditable()) {
            throw new BadRequestException("Readonly dataset");
        }
    }

    public Dataset addRow(UUID datasetId,
                          Map<@NotNull String, @NotNull String> row,
                          Map<@NotNull String, @NotNull String> prediction,
                          Map<@NotNull String, @NotNull String> calculated) throws IOException {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        ensureEditable(dataset);

        addDatasetRow(dataset, true, row, prediction, calculated);
        addDatasetRow(dataset, false, row, prediction, calculated);

        // TODO: update file size
        dataset.setNumberOfRows(dataset.getNumberOfRows() + 1);
        datasetRepository.save(dataset);

        return dataset;

    }

    public Dataset deleteRow(UUID datasetId, int rowId) throws IOException {
        Dataset dataset = datasetRepository.getMandatoryById(datasetId);
        ensureEditable(dataset);

        deleteDatasetRow(dataset, rowId, true);
        deleteDatasetRow(dataset, rowId, false);

        // TODO: update file size
        dataset.setNumberOfRows(dataset.getNumberOfRows() - 1);
        datasetRepository.save(dataset);

        return dataset;
    }

    private void addDatasetRow(Dataset dataset,
                               boolean sample,
                               Map<@NotNull String, @NotNull String> row,
                               Map<@NotNull String, @NotNull String> prediction,
                               Map<@NotNull String, @NotNull String> calculated) throws IOException {
        CsvOperationResult result = updateDataset(locationService.resolvedDatasetCsvPath(dataset, sample), null, List.of(row));

        for (Inspection inspection : dataset.getInspections()) {
            updateCsvIfExists(locationService.resolvedInspectionPredictionsPath(inspection, sample), result, List.of(prediction));
            updateCsvIfExists(locationService.resolvedInspectionCalculatedPath(inspection, sample), result, List.of(calculated));
        }
    }

    private void deleteDatasetRow(Dataset dataset, int rowId, boolean sample) throws IOException {
        String rowIdStr = String.valueOf(rowId);
        CsvOperationResult result = updateDataset(locationService.resolvedDatasetCsvPath(dataset, sample),
            record -> record.get(GISKARD_DATASET_UID_COLUMN).equals(rowIdStr), Collections.emptyList());

        for (Inspection inspection : dataset.getInspections()) {
            updateCsvIfExists(locationService.resolvedInspectionPredictionsPath(inspection, sample), result, Collections.emptyList());
            updateCsvIfExists(locationService.resolvedInspectionCalculatedPath(inspection, sample), result, Collections.emptyList());
        }
    }

    private CsvOperationResult updateDataset(Path path, Predicate<CSVRecord> shouldKeepRow,
                                             List<Map<String, String>> appendedRows) throws IOException {
        int curRow = 0;

        final Path tmp = Files.createTempFile("gsk", "csv.zst");

        try (CSVParser parser = new CSVParser(new BufferedReader(new InputStreamReader(new ZstdInputStream(Files.newInputStream(path)))), READER_FORMAT);
             CSVPrinter printer = new CSVPrinter(new BufferedWriter(new OutputStreamWriter(new ZstdOutputStream(Files.newOutputStream(tmp)))),
                 WRITER_FORMAT.builder().setHeader(parser.getHeaderNames().toArray(String[]::new)).build())) {
            CsvOperationResult result = new CsvOperationResult(parser.getHeaderNames());

            for (Iterator<CSVRecord> it = parser.iterator(); it.hasNext(); curRow++) {
                CSVRecord record = it.next();

                if (shouldKeepRow != null && shouldKeepRow.test(record)) {
                    printer.printRecord(record);
                    result.writeRow(Integer.parseInt(record.get(GISKARD_DATASET_UID_COLUMN)));
                } else {
                    result.deleteRow(curRow);
                }
            }

            for (Map<String, String> row : appendedRows) {
                row = new HashMap<>(row);
                row.put(GISKARD_DATASET_UID_COLUMN, Integer.toString(++result.maxGskUid));
                printer.printRecord(result.headers.stream().map(row::get));
            }

            return result;
        } finally {
            Files.delete(path);
            Files.move(tmp, path);
        }
    }

    private void updateCsvIfExists(Path path, CsvOperationResult result,
                                   List<Map<String, String>> appendedRows) throws IOException {
        if (!Files.exists(path)) {
            return;
        }

        final Path tmp = Files.createTempFile("gsk", "csv");

        int currentRow = 0;
        try (CSVParser parser = new CSVParser(Files.newBufferedReader(path), READER_FORMAT);
             CSVPrinter printer = new CSVPrinter(Files.newBufferedWriter(tmp),
                 WRITER_FORMAT.builder().setHeader(parser.getHeaderNames().toArray(String[]::new)).build())) {
            Iterator<CSVRecord> it = parser.iterator();

            for (int nextDeletedRow : result.deletedRows) {
                while (currentRow++ < nextDeletedRow) {
                    printer.printRecord(it.next());
                }
                it.next();
            }

            while (it.hasNext()) {
                printer.printRecord(it.next());
            }

            for (Map<String, String> row : appendedRows) {
                printer.printRecord(result.headers.stream().map(row::get));
            }
        } finally {
            Files.delete(path);
            Files.move(tmp, path);
        }
    }

    private static class CsvOperationResult {
        private final List<String> headers;
        private final SortedSet<Integer> deletedRows = new TreeSet<>();
        private int maxGskUid = -1;

        private CsvOperationResult(List<String> headers) {
            this.headers = headers;
        }

        public void deleteRow(int index) {
            deletedRows.add(index);
        }

        public void writeRow(int uid) {
            maxGskUid = Math.max(maxGskUid, uid);
        }
    }

}
