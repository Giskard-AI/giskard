package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSEchoMsgDTO;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class MLWorkerService {
    public static final String HEARTBEAT_MESSAGE = "hb";
    private final Logger log = LoggerFactory.getLogger(MLWorkerService.class);
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;

    @Scheduled(fixedRateString = "${giskard.external-worker-heartbeat-interval-seconds:60}", timeUnit = TimeUnit.SECONDS)
    public void sendHeartbeatToConnectedWorkers() {
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL)) {
            log.debug("Executing ML Worker heartbeat");
            MLWorkerWSEchoMsgDTO echoMsg = MLWorkerWSEchoMsgDTO.builder()
                .msg(HEARTBEAT_MESSAGE)
                .build();
            MLWorkerWSBaseDTO result= mlWorkerWSCommService.performAction(
                MLWorkerID.EXTERNAL,
                MLWorkerWSAction.ECHO,
                echoMsg
            );
            if (result instanceof MLWorkerWSEchoMsgDTO reply) {
                if (!HEARTBEAT_MESSAGE.equals(reply.getMsg())) {
                    log.warn("ML Worker heartbeat returned unexpected result: {}", reply.getMsg());
                }
            } else {
                log.warn("Cannot get ML Worker heartbeat message");
            }
        }
    }
}
