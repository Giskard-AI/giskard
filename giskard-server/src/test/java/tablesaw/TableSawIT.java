package tablesaw;

import ai.giskard.IntegrationTest;
import lombok.NonNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import tech.tablesaw.api.*;
import tech.tablesaw.io.csv.CsvReadOptions;
import tech.tablesaw.selection.Selection;

import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Collections;
import java.util.stream.Collectors;

import static ai.giskard.domain.ml.table.TableConstants.BORDERLINE_THRESHOLD;
import static org.assertj.core.api.AssertionsForClassTypes.assertThat;


@IntegrationTest
public class TableSawIT {

    @Value("classpath:bucket/my-dataset.csv")
    Resource dataFile;

    @Value("classpath:bucket/probs.csv")
    Resource probsFile;


    /**
     * Filter table on stream
     *
     * @throws Exception
     */
    @Test
    void filterStream() throws Exception {
        InputStreamReader reader = new InputStreamReader(
            dataFile.getInputStream());
        Table table = Table.read()
            .usingOptions(CsvReadOptions.builder(reader));
        basicFilter(table);
    }

    @Test
    void filterFile() throws Exception {
        Table table = Table.read()
            .usingOptions(CsvReadOptions.builder(dataFile.getFile()));
        basicFilter(table);
    }

    /**
     * Basic filter on table
     *
     * @param table table to filter
     */
    void basicFilter(@NonNull Table table) {
        StringColumn column = table.stringColumn("account_check_status");
        Selection startSelection = column.startsWith("<");
        Table onlyInferior = table.where(startSelection);
        assertThat(table.rowCount()).isGreaterThan(onlyInferior.rowCount());
    }


    @Nested
    class FilterIT {
        private Table table;
        private Table probsTable;
        private DoubleColumn finalColumn;
        private IntColumn labelColumn;
        private DoubleColumn targetColumn;
        private Table probsWithoutTargetTable;

        @BeforeEach
        public void init() throws IOException {
            table = Table.read()
                .usingOptions(CsvReadOptions.builder(dataFile.getFile()));
            probsTable = Table.read()
                .usingOptions(CsvReadOptions.builder(probsFile.getFile()));
            targetColumn = probsTable.doubleColumn("predictions_Default");
            labelColumn = (IntColumn) table.column("Default");
            finalColumn = labelColumn.multiply(targetColumn);
            probsWithoutTargetTable=probsTable.rejectColumns(targetColumn.name());
        }

        /**
         * Filter to get borderline examples, correct examples with less than 0.1 prob difference with the second one.
         * Here filter is done on every column to get the results
         */
        @Test
        void filterBorderline() {
            Selection selection = finalColumn.isGreaterThanOrEqualTo(0.5);
            probsTable.columnsOfType(ColumnType.DOUBLE).stream().forEach(x -> selection.and(((DoubleColumn) x).subtract(targetColumn).abs().isLessThan(BORDERLINE_THRESHOLD)));
            Table filteredTable = table.where(selection);
            System.out.println("Number of rows after selection : " + table.where(selection).rowCount());
            assertThat(filteredTable.rowCount()).isEqualTo(20);
        }

        /**
         * Here filter is done by first substracting the target column to all other columns and take the absolute
         * Then taking the max of these columns and filter by borderline threshold.
         */
        @Test
        void filterBorderline2()  {
            Table absDiffTable = Table.create("absDiffTable");
            probsWithoutTargetTable.columnsOfType(ColumnType.DOUBLE).stream().forEach(x -> absDiffTable.addColumns(((DoubleColumn) x).subtract(targetColumn).abs()));
            DoubleColumn _max = DoubleColumn.create("max", absDiffTable.stream().mapToDouble(row -> Collections.max(row.columnNames().stream().map(name -> row.getDouble(name)).collect(Collectors.toList()))));
            // TODO Check if we need the correct ones
            Selection selection = _max.isLessThan(BORDERLINE_THRESHOLD).and(finalColumn.isGreaterThanOrEqualTo(0.5));
            Table finalTable = table.addColumns(_max).where(selection).sortAscendingOn(_max.name());
            System.out.println("Number of rows after selection : " + finalTable.rowCount());
            assertThat(finalTable.rowCount()).isEqualTo(20);
        }

        /**
         * Here filter is done first by taking the max of all but target columns
         * Then substract by the target column and taking the absolute
         * Then filter by borderline threshold.
         */
        @Test
        void filterBorderline3()  {
            DoubleColumn _max = DoubleColumn.create("max", probsWithoutTargetTable.stream().mapToDouble(row -> Collections.max(row.columnNames().stream().map(name -> row.getDouble(name)).collect(Collectors.toList()))));
            DoubleColumn absDiff=_max.subtract(targetColumn).abs();
            Selection selection= absDiff.isLessThan(BORDERLINE_THRESHOLD).and(finalColumn.isGreaterThanOrEqualTo(0.5));
            Table finalTable = table.addColumns(absDiff).where(selection).sortAscendingOn(absDiff.name());
            System.out.println("Number of rows after selection : " + finalTable.rowCount());
            assertThat(finalTable.rowCount()).isEqualTo(20);
        }
    }

}
