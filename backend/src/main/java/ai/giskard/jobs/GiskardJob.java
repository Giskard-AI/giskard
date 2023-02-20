package ai.giskard.jobs;

import ai.giskard.web.dto.JobDTO;

import java.util.UUID;

public interface GiskardJob extends Runnable {
    UUID getUUID();
    JobDTO toDTO();


}
