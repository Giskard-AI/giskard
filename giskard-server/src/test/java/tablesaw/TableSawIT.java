package tablesaw;

import ai.giskard.IntegrationTest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.Table;
import tech.tablesaw.io.csv.CsvReadOptions;
import tech.tablesaw.selection.Selection;

import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.file.Paths;

import static org.assertj.core.api.AssertionsForClassTypes.assertThat;


@IntegrationTest
public class TableSawIT {

    @Value("classpath:bucket/my-dataset.csv")
    Resource resourceFile;

    /**
     * Filter table on stream
     *
     * @throws Exception
     */
    @Test
    void filterStream() throws Exception {
        InputStreamReader reader = new InputStreamReader(
            resourceFile.getInputStream());
        Table table = Table.read()
            .usingOptions(CsvReadOptions.builder(reader));
        StringColumn column = table.stringColumn("account_check_status");
        Selection startSelection = column.startsWith("<");
        Table onlyInferior = table.where(startSelection);

        assertThat(table.rowCount()).isGreaterThan(onlyInferior.rowCount());

    }


}
