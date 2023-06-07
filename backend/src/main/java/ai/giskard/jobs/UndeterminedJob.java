package ai.giskard.jobs;

import ai.giskard.domain.MLWorkerType;
import ai.giskard.web.dto.JobDTO;
import lombok.RequiredArgsConstructor;
import org.slf4j.LoggerFactory;

import java.util.Date;
import java.util.UUID;

@RequiredArgsConstructor
public class UndeterminedJob implements GiskardJob {
    private static final org.slf4j.Logger logger = LoggerFactory.getLogger(UndeterminedJob.class);
    private final Runnable runnable;
    private final Date scheduledDate = new Date();
    private final UUID uuid = UUID.randomUUID();
    private JobState state = JobState.SCHEDULED;
    private final long projectId;
    private final JobType jobType;
    private final MLWorkerType mlWorkerType;

    @Override
    public void run() {
        try {
            state = JobState.RUNNING;
            runnable.run();
            state = JobState.SUCCESS;
        } catch (Exception e) {
            logger.error("Failed to execute ML Worker job: {}", e.getMessage());
            state = JobState.ERROR;
        }
    }

    @Override
    public UUID getUUID() {
        return uuid;
    }

    @Override
    public JobDTO toDTO() {
        return new JobDTO(scheduledDate, state, null, projectId, jobType, mlWorkerType);
    }
}
