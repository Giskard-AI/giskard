package ai.giskard.jobs;

import ai.giskard.domain.MLWorkerType;

public interface MLWorkerJob extends GiskardJob {

    MLWorkerType getMLWorkerType();

}
