package ai.giskard.service;

import lombok.RequiredArgsConstructor;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import java.util.Arrays;

/**
 * Service for download files.
 * <p>
 * We use the {@link Async} annotation to send emails asynchronously.
 */
@RequiredArgsConstructor
@Service
public class DownloadService {

    final FileUploadService fileUploadService;

    /**
     * Read file from zst stream and send it to the response
     *
     * @param path path to the file
     * @param suffix suffix name of the file, extension name
     * @return response entity
     * @throws IOException
     */
    public ResponseEntity<Resource> download(Path path, String suffix) throws IOException {
        InputStream inputStream = fileUploadService.decompressFileToStream(path);
        ByteArrayResource resource = new ByteArrayResource(inputStream.readAllBytes());
        HttpHeaders header = new HttpHeaders();
        // TODO Get original filename/extension from upload?
        String fileName = path.getFileName().toString().replaceAll("\\.zst$", suffix);
        header.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + fileName);
        header.setAccessControlExposeHeaders(Arrays.asList(HttpHeaders.CONTENT_DISPOSITION));
        return ResponseEntity.ok()
            .headers(header)
            .contentType(MediaType.parseMediaType("text/csv"))
            .contentLength(resource.contentLength())
            .body(resource);
    }
}
