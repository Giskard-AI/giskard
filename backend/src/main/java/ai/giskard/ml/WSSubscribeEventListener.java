package ai.giskard.ml;

import ai.giskard.config.WebSocketConfig;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationListener;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionSubscribeEvent;

@Component
@RequiredArgsConstructor
public class WSSubscribeEventListener implements ApplicationListener<SessionSubscribeEvent> {
    private final Logger logger = LoggerFactory.getLogger(WSSubscribeEventListener.class.getName());

    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;

    @Override
    public void onApplicationEvent(SessionSubscribeEvent event) {
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.INTERNAL))
            mlWorkerWSCommService.notifyMaxReplyPayloadLength(MLWorkerID.INTERNAL,
                WebSocketConfig.MAX_REPLY_PAYLOAD_SIZE);
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL))
            mlWorkerWSCommService.notifyMaxReplyPayloadLength(MLWorkerID.EXTERNAL,
                WebSocketConfig.MAX_REPLY_PAYLOAD_SIZE);
    }
}
