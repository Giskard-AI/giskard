package ai.giskard.web.rest.controllers;

import ai.giskard.service.ml.MLWorkerCacheService;
import ai.giskard.web.dto.CatalogDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class CatalogController {

    private final MLWorkerCacheService mlWorkerCacheService;

    @GetMapping("/project/{projectId}/catalog")
    public CatalogDTO getCatalog(@PathVariable long projectId) {
        return mlWorkerCacheService.getCatalog(projectId);
    }

}
