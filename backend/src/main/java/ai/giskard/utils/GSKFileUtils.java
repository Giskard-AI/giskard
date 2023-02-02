package ai.giskard.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;


public class GSKFileUtils {
    private GSKFileUtils() {
    }

    private static final Logger log = LoggerFactory.getLogger(GSKFileUtils.class);

    public static ByteArrayOutputStream createZipArchive(String directoryPath) throws IOException {
        AtomicBoolean exceptionOccurred = new AtomicBoolean(false);
        Path directory = Paths.get(directoryPath);
        if (!Files.isDirectory(directory)) {
            throw new IllegalArgumentException("Not a directory: " + directoryPath);
        }

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (ZipOutputStream zos = new ZipOutputStream(baos);
             Stream<Path> files = Files.walk(directory)) {

            files
                .filter(path -> !Files.isDirectory(path))
                .forEach(path -> {
                    ZipEntry entry = new ZipEntry(directory.relativize(path).toString());
                    try {
                        zos.putNextEntry(entry);
                        Files.copy(path, zos);
                        zos.closeEntry();
                    } catch (IOException e) {
                        log.error("Failed to archive resource file: {}", path.toAbsolutePath(), e);
                        exceptionOccurred.set(true);
                    }
                });
        }
        if (exceptionOccurred.get()) {
            throw new IOException("Failed to create artifact archive");
        }
        return baos;
    }
}

