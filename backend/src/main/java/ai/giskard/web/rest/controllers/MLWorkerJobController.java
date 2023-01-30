package ai.giskard.web.rest.controllers;

import ai.giskard.service.JobService;
import ai.giskard.web.dto.JobDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

import static ai.giskard.security.AuthoritiesConstants.ADMIN;

@RestController
@RequestMapping("/api/v2/jobs")
@RequiredArgsConstructor
public class MLWorkerJobController {

    private final JobService jobService;

    @GetMapping("running")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public List<JobDTO> getRunningWorkerJobs() {
        return jobService.getRunningWorkerJobs();
    }

    @GetMapping("{jobUuid}")
    @PreAuthorize("hasAuthority(\"" + ADMIN + "\")")
    public JobDTO trackJob(@PathVariable UUID jobUuid) {
        return jobService.getProgress(jobUuid);
    }

}
