package ai.giskard.web.rest.project;

import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.service.dto.ml.ModelDTO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v2/project/models")
public class ModelsController {
    private ModelRepository modelRepository;

    public ModelsController(ModelRepository modelRepository) {
        this.modelRepository = modelRepository;
    }

    @GetMapping("")
    public List<ModelDTO> listProjectModels(@RequestParam @NotNull Long projectId) {
        return modelRepository.findAllByProjectId(projectId).stream().map(ModelDTO::new).collect(Collectors.toList());
    }
}
