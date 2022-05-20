package tablesaw;

import ai.giskard.IntegrationTest;
import ai.giskard.config.ApplicationProperties;
import lombok.NonNull;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;
import tech.tablesaw.selection.Selection;

import java.io.InputStreamReader;

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


}
