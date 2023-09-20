package ai.giskard.utils;

import com.github.luben.zstd.ZstdInputStream;
import com.github.luben.zstd.ZstdOutputStream;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVPrinter;
import org.apache.commons.csv.CSVRecord;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Iterator;
import java.util.List;


public class CsvEditStream implements Closeable {

    private final Path path;
    private final CSVParser parser;
    private final CSVPrinter printer;

    public CsvEditStream(Path path, boolean compressed) throws IOException {
        this.path = path;
        parser = fileParser(path, compressed);
        printer = filePrinter(path.resolveSibling(path.getFileName() + ".tmp"), parser.getHeaderNames(), compressed);
    }

    private CSVParser fileParser(Path path, boolean compressed) throws IOException {
        InputStream inputStream = Files.newInputStream(path);
        if (compressed) {
            inputStream = new ZstdInputStream(inputStream);
        }

        Reader reader = new BufferedReader(new InputStreamReader(inputStream));

        CSVFormat csvFormat = CSVFormat.DEFAULT.builder()
            .setHeader()
            .setSkipHeaderRecord(true)
            .build();

        return new CSVParser(reader, csvFormat);
    }

    private CSVPrinter filePrinter(Path path, List<String> header, boolean compressed) throws IOException {
        OutputStream outputStream = Files.newOutputStream(path);
        if (compressed) {
            outputStream = new ZstdOutputStream(outputStream);
        }

        Writer writer = new BufferedWriter(new OutputStreamWriter(outputStream));
        CSVFormat csvFormat = CSVFormat.DEFAULT.builder()
            .setHeader(header.toArray(new String[0]))
            .setSkipHeaderRecord(false)
            .build();

        return new CSVPrinter(writer, csvFormat);
    }

    public Iterator<CSVRecord> iterator() {
        return parser.iterator();
    }

    public void write(CSVRecord record) throws IOException {
        printer.printRecord(record.stream());
    }

    @Override
    public void close() throws IOException {
        parser.close();
        printer.close();
        Files.delete(path);
        Files.move(path.resolveSibling(path.getFileName() + ".tmp"), path);
    }
}
