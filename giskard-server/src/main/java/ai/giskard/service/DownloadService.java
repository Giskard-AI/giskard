package ai.giskard.service;

import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;

/**
 * Service for download files.
 * <p>
 * We use the {@link Async} annotation to send emails asynchronously.
 */
@RequiredArgsConstructor
@Service
public class DownloadService {

    final FileUploadService fileUploadService;

    public void download(Path path, HttpServletResponse response) throws IOException {
        InputStream inputStream=fileUploadService.decompressFileToStream(path);
        inputStream.transferTo(response.getOutputStream());
        inputStream.close();
        response.addHeader("Content-disposition", "attachment; filename=" + path.getFileName());
        response.setContentType("application/csv");
        response.flushBuffer();

    }
}
