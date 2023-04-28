package ai.giskard.web.rest.controllers;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.PushService;
import ai.giskard.web.dto.PushDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/")
public class PushController {

    private final ModelRepository modelRepository;
    private final PermissionEvaluator permissionEvaluator;
    private final DatasetRepository datasetRepository;
    private final PushService pushService;


    @GetMapping("/pushes/{modelId}/{datasetId}/{idx}")
    public List<PushDTO> getPushes(@PathVariable @NotNull UUID modelId, @PathVariable @NotNull UUID datasetId, @PathVariable @NotNull int idx) {
        ProjectModel model = modelRepository.getById(modelId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());
        Dataset dataset = datasetRepository.getById(datasetId);
        return pushService.getPushes(
            model,
            dataset,
            idx
        );
    }

    @PostMapping("/push/apply")
    public void applyPushSuggestion() {
        // TODO: Check all types of suggestions we have ?
    }
}
