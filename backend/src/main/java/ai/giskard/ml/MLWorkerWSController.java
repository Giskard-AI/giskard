package ai.giskard.ml;

import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;

@Controller
@RequiredArgsConstructor
public class MLWorkerWSController {
    private final Logger logger = LoggerFactory.getLogger(MLWorkerWSController.class.getName());

    private final MLWorkerWSService mlWorkerWSService;

    @MessageMapping("/ml-worker/{workerId}/rep")
    public void onReplyReceived(@DestinationVariable String workerId, MLWorkerReplyDTO body) {
        logger.info("Received rep from Worker " + workerId + " " + body.getId() + " " + body.getAction());
        // mlWorkerWSService notifies the listener
        mlWorkerWSService.attachResult(body.getId(), body.getPayload());
    }
}
