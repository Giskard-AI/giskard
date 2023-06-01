package ai.giskard.service;

import ai.giskard.domain.ArtifactType;
import lombok.RequiredArgsConstructor;
import org.apache.commons.compress.compressors.CompressorException;
import org.apache.commons.compress.compressors.CompressorStreamFactory;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FileUploadService {
    private final FileLocationService locationService;
    private final Logger log = LoggerFactory.getLogger(FileUploadService.class);


    public InputStream decompressFileToStream(Path compressedInputPath) {
        log.info("Decompressing file {}", compressedInputPath);
        try {
            final InputStream compressedInputStream = Files.newInputStream(compressedInputPath);
            return new CompressorStreamFactory().createCompressorInputStream(CompressorStreamFactory.ZSTANDARD, compressedInputStream);
        } catch (IOException e) {
            throw new GiskardRuntimeException(String.format("Failed to read file to %s", compressedInputPath), e);
        } catch (CompressorException e) {
            throw new GiskardRuntimeException(String.format("Failed to decompress input when reading %s", compressedInputPath), e);
        }
    }


    public void saveArtifact(InputStream uploadedStream, String projectKey, ArtifactType artifactType, String artifactId, String path) throws IOException {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.toDirectoryName(), artifactId));
        Path artifactPath = artifactDirectory.resolve(path);
        Path tempFile = artifactPath.resolveSibling(artifactPath.getFileName() + ".tmp");

        if (!artifactPath.normalize().startsWith(artifactDirectory.normalize())) {
            throw new GiskardRuntimeException(String.format("Artifact path %s isn't relative to artifact directory", path));
        }
        if (artifactPath.toFile().exists()) {
            log.info("File already exists {}", locationService.giskardHome().relativize(artifactPath));
            return;
        }
        FileUtils.forceMkdirParent(artifactPath.toFile());
        FileUtils.deleteQuietly(tempFile.toFile());

        try (OutputStream out = new FileOutputStream(tempFile.toFile())) {
            IOUtils.copy(uploadedStream, out);
        }
        Files.move(tempFile, artifactPath);
    }

    public Set<String> listArtifacts(String projectKey, ArtifactType artifactType, String artifactId) {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.toDirectoryName(), artifactId));
        return FileUtils.listFiles(artifactDirectory.toFile(), null, true).stream()
            .map(file -> artifactDirectory.relativize(file.toPath()).toString())
            .collect(Collectors.toSet());
    }

    public InputStream getArtifactStream(String projectKey, ArtifactType artifactType, String artifactId, String path) throws FileNotFoundException {
        Path artifactDirectory = locationService.resolvedProjectHome(projectKey).resolve(Path.of(artifactType.toDirectoryName(), artifactId));
        Path artifactPath = artifactDirectory.resolve(path);
        return new FileInputStream(artifactPath.toFile());
    }
}
