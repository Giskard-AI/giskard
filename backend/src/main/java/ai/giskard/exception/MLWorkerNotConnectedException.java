package ai.giskard.exception;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.service.GiskardRuntimeException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MLWorkerNotConnectedException extends GiskardRuntimeException {
    private static final Logger logger = LoggerFactory.getLogger(MLWorkerNotConnectedException.class);

    public MLWorkerNotConnectedException(MLWorkerID id, Exception e, Logger log) {
        super(
            String.format("Failed to establish a connection with %s ML Worker.%nStart it by running %s",
                id == MLWorkerID.INTERNAL ? "internal" : "external",
                id == MLWorkerID.INTERNAL ? "giskard server restart worker" : "`giskard worker start -u GISKARD_ADDRESS` in the terminal of the machine that will execute the model. For more details refer to documentation: https://docs.giskard.ai/start/guides/installation/ml-worker"
            ), e
        );
        log.warn("Failed to connect to ML Worker client", e);
    }

    public MLWorkerNotConnectedException(MLWorkerID id, Exception e) {
        this(id, e, logger);
    }

    public MLWorkerNotConnectedException(MLWorkerID id, Logger log) {
        this(id, new Exception(), log);
    }

    public MLWorkerNotConnectedException(MLWorkerID id) {
        this(id, new Exception(), logger);
    }
}
