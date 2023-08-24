package ai.giskard.service;

import ai.giskard.domain.MLWorkerType;
import ai.giskard.jobs.GiskardJob;
import ai.giskard.jobs.JobState;
import ai.giskard.jobs.JobType;
import ai.giskard.jobs.UndeterminedJob;
import ai.giskard.web.dto.JobDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.core.task.AsyncTaskExecutor;
import org.springframework.stereotype.Service;

import jakarta.persistence.EntityNotFoundException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class JobService {

    private final AsyncTaskExecutor taskExecutor;
    private final Map<UUID, GiskardJob> jobs = new ConcurrentHashMap<>();

    public UUID undetermined(Runnable runnable, long projectId, JobType jobType, MLWorkerType mlWorkerType) {
        return schedule(new UndeterminedJob(runnable, projectId, jobType, mlWorkerType));
    }

    private UUID schedule(GiskardJob job) {
        jobs.put(job.getUUID(), job);
        taskExecutor.submit(job);
        return job.getUUID();
    }

    public JobDTO getProgress(UUID uuid) {
        GiskardJob job = jobs.get(uuid);

        if (job == null) {
            throw new EntityNotFoundException();
        }

        JobDTO dto = job.toDTO();

        if (JobState.SUCCESS.equals(dto.getState()) || JobState.ERROR.equals(dto.getState())) {
            jobs.remove(uuid);
        }

        return dto;
    }

    public List<JobDTO> getRunningWorkerJobs() {
        return jobs.values().stream()
            .map(GiskardJob::toDTO)
            .toList();
    }

}
