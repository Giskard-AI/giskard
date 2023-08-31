package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ArtifactType;
import ai.giskard.service.FileUploadService;
import lombok.RequiredArgsConstructor;
import org.apache.commons.io.IOUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.HandlerMapping;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.util.Set;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class UploadController {
    private static final String GLOBAL_KEY = "global";

    private final FileUploadService uploadService;

    @GetMapping("artifact-info/global/{artifactType}/{artifactId}")
    public Set<String> getGlobalArtifactInfo(@PathVariable String artifactType,
                                             @PathVariable String artifactId) {

        return uploadService.listArtifacts(GLOBAL_KEY, ArtifactType.fromDirectoryName(artifactType), artifactId);
    }

    @GetMapping("artifact-info/{projectKey}/{artifactType}/{artifactId}")
    @PreAuthorize("@permissionEvaluator.canReadProjectKey(#projectKey)")
    public Set<String> getArtifactInfo(@PathVariable String projectKey,
                                       @PathVariable String artifactType,
                                       @PathVariable String artifactId) {

        return uploadService.listArtifacts(projectKey, ArtifactType.fromDirectoryName(artifactType), artifactId);
    }

    @GetMapping("artifacts/global/{artifactType}/{artifactId}/**")
    public void downloadGlobalArtifact( @PathVariable String artifactType,
                                 @PathVariable String artifactId,
                                 HttpServletRequest request,
                                 HttpServletResponse response) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);

        try (InputStream artifactStream = uploadService.getArtifactStream(GLOBAL_KEY, ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath)) {
            IOUtils.copy(artifactStream, response.getOutputStream());
            response.flushBuffer();
        }
    }

    @GetMapping("artifacts/{projectKey}/{artifactType}/{artifactId}/**")
    @PreAuthorize("@permissionEvaluator.canReadProjectKey(#projectKey)")
    public void downloadArtifact(@PathVariable String projectKey,
                                 @PathVariable String artifactType,
                                 @PathVariable String artifactId,
                                 HttpServletRequest request,
                                 HttpServletResponse response) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);

        try (InputStream artifactStream = uploadService.getArtifactStream(projectKey, ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath)) {
            IOUtils.copy(artifactStream, response.getOutputStream());
            response.flushBuffer();
        }
    }

    @PostMapping("artifacts/global/{artifactType}/{artifactId}/**")
    public ResponseEntity<Void> uploadGlobalArtifact(@PathVariable String artifactType,
                                               @PathVariable String artifactId,
                                               HttpServletRequest request) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);


        try (InputStream uploadedStream = request.getInputStream()) {
            uploadService.saveArtifact(uploadedStream, GLOBAL_KEY, ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath);
        }

        return new ResponseEntity<>(HttpStatus.OK);
    }
    @PostMapping("artifacts/{projectKey}/{artifactType}/{artifactId}/**")
    @PreAuthorize("@permissionEvaluator.canWriteProjectKey(#projectKey)")
    public ResponseEntity<Void> uploadArtifact(@PathVariable String projectKey,
                                               @PathVariable String artifactType,
                                               @PathVariable String artifactId,
                                               HttpServletRequest request) throws IOException {
        String path = (String) request.getAttribute(HandlerMapping.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE);
        String matchPattern = (String) request.getAttribute(HandlerMapping.BEST_MATCHING_PATTERN_ATTRIBUTE);
        String resoursePath = new AntPathMatcher().extractPathWithinPattern(matchPattern, path);


        try (InputStream uploadedStream = request.getInputStream()) {
            uploadService.saveArtifact(uploadedStream, projectKey, ArtifactType.fromDirectoryName(artifactType), artifactId, resoursePath);
        }

        return new ResponseEntity<>(HttpStatus.OK);
    }
}
