package ai.giskard.service;

import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.compress.compressors.CompressorException;
import org.apache.commons.compress.compressors.CompressorInputStream;
import org.apache.commons.compress.compressors.CompressorOutputStream;
import org.apache.commons.compress.compressors.CompressorStreamFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

@Service
@RequiredArgsConstructor
public class FileUploadService {
    final ModelRepository modelRepository;
    final GiskardMapper giskardMapper;

    final ProjectService projectService;
    final ProjectRepository projectRepository;

    private final Logger log = LoggerFactory.getLogger(FileUploadService.class);



    private void streamToCompressedFile(InputStream inputStream, Path outputPath) {
        try {
            OutputStream outStream = Files.newOutputStream(outputPath);
            CompressorOutputStream cos = new CompressorStreamFactory().
                createCompressorOutputStream(CompressorStreamFactory.ZSTANDARD, outStream);
            inputStream.transferTo(cos);
            cos.close();
            log.info("Saved file: {}", outputPath);

        } catch (IOException e) {
            throw new RuntimeException(String.format("Failed to write file to %s", outputPath), e);
        } catch (CompressorException e) {
            throw new RuntimeException(String.format("Failed to compress output when writing %s", outputPath), e);
        }
    }
    public InputStream decompressFileToStream(Path compressedInputPath) {
        try {
            final InputStream compressedInputStream = Files.newInputStream(compressedInputPath);
            CompressorInputStream in = new CompressorStreamFactory()
                .createCompressorInputStream(CompressorStreamFactory.ZSTANDARD, compressedInputStream);
            return in;
            //long transferredBytes = in.transferTo(outputStream);
            //in.close();
            //log.info("Read file: {} ({} bytes)", compressedInputPath, transferredBytes);

        } catch (IOException e) {
            throw new RuntimeException(String.format("Failed to read file to %s", compressedInputPath), e);
        } catch (CompressorException e) {
            throw new RuntimeException(String.format("Failed to decompress input when reading %s", e), e);
        }
    }

}
