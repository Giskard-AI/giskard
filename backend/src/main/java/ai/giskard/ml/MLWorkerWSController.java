package ai.giskard.ml;

import ai.giskard.ml.dto.MLWorkerReplyDTO;
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
        logger.debug("Received rep from Worker {} {} {}", workerId, body.getId(), body.getAction());
        logger.debug("Fragment count: {}, Fragment index: {}, {}/{}, Type: {}",
            body.getFragmentCount(), body.getFragmentIndex(),
            body.getIndex(), body.getTotal(), body.getType());

        if (body.getFragmentCount() <= 1) {
            if (body.getType() == MLWorkerReplyType.FINISH) {
                // Message is completed, notifies the listener
                if (body.getIndex() > 0) {
                    // Last message in a multiple-shot action
                    mlWorkerWSService.attachResult(body.getId(), body.getPayload(),
                        true, body.getIndex(), body.getTotal());
                } else {
                    mlWorkerWSService.attachResult(body.getId(), body.getPayload());
                }
            } else if (body.getType() == MLWorkerReplyType.UPDATE) {
                // Message is completed, update the listener
                mlWorkerWSService.attachResult(body.getId(), body.getPayload(),
                    false, body.getIndex(), body.getTotal());
            }
        } else {
            // Message is incomplete: fragment it
            if (body.getType() == MLWorkerReplyType.FINISH) {
                // Message is completed, notifies the listener
                mlWorkerWSService.appendReply(
                    body.getId(),
                    body.getFragmentIndex(),
                    body.getFragmentCount(),
                    body.getPayload()
                );
            } else if (body.getType() == MLWorkerReplyType.UPDATE) {
                mlWorkerWSService.appendReply(
                    body.getId(),
                    body.getFragmentIndex(),
                    body.getFragmentCount(),
                    body.getIndex(),
                    body.getTotal(),
                    body.getPayload()
                );
            }
        }

    }
}
