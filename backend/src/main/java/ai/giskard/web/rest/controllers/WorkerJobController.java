package ai.giskard.web.rest.controllers;

import ai.giskard.service.WorkerJobService;
import ai.giskard.web.dto.ml.WorkerJobDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

@RestController
@RequestMapping("/api/v2/worker/jobs")
@RequiredArgsConstructor
public class WorkerJobController {

    private final WorkerJobService workerJobService;

    @GetMapping("running")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public List<WorkerJobDTO> getRunningWorkerJobs() {
        return workerJobService.getRunningWorkerJobs();
    }

}
