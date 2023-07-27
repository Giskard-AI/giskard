package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ArtifactType;
import ai.giskard.service.FileUploadService;
import lombok.RequiredArgsConstructor;
import org.apache.commons.io.IOUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.HandlerMapping;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.util.Set;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class UploadController {

    private final FileUploadService uploadService;

    // TODO: check usages and fix permissions, optional filter per project?
    @GetMapping("artifact-info/{artifactType}/{artifactId}")
    public Set<String> getGlobalArtifactInfo(@PathVariable String artifactType,
                                             @PathVariable String artifactId) {

        return uploadService.listArtifacts(ArtifactType.fromDirectoryName(artifactType), artifactId);
    }

    @GetMapping("artifacts/{artifactType}/{artifactId}/**")
    public void downloadGlobalArtifact(@PathVariable String artifactType,
                                       @PathVariable String artifactId,
                                       HttpServletRequest request,
                                       HttpServletResponse response) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);

        try (InputStream artifactStream = uploadService.getArtifactStream(ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath)) {
            IOUtils.copy(artifactStream, response.getOutputStream());
            response.flushBuffer();
        }
    }

    @PostMapping("artifacts/{artifactType}/{artifactId}/**")
    public ResponseEntity<Void> uploadGlobalArtifact(@PathVariable String artifactType,
                                               @PathVariable String artifactId,
                                               HttpServletRequest request) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);


        try (InputStream uploadedStream = request.getInputStream()) {
            uploadService.saveArtifact(uploadedStream, ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath);
        }

        return new ResponseEntity<>(HttpStatus.OK);
    }
}
