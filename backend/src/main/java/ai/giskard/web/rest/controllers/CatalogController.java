package ai.giskard.web.rest.controllers;

import ai.giskard.service.ml.MLWorkerCacheService;
import ai.giskard.web.dto.CatalogDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class CatalogController {

    private final MLWorkerCacheService mlWorkerCacheService;

    @GetMapping("/catalog")
    public CatalogDTO getCatalog(@RequestParam long projectId) {
        return mlWorkerCacheService.getCatalog(projectId);
    }

}
