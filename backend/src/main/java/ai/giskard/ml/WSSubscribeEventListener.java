package ai.giskard.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.config.WebSocketConfig;
import ai.giskard.service.ml.MLWorkerWSCommService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationListener;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionSubscribeEvent;

@Component
@RequiredArgsConstructor
public class WSSubscribeEventListener implements ApplicationListener<SessionSubscribeEvent> {
    private final Logger logger = LoggerFactory.getLogger(WSSubscribeEventListener.class.getName());

    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final ApplicationProperties applicationProperties;

    @Override
    public void onApplicationEvent(SessionSubscribeEvent event) {
        StompHeaderAccessor headerAccessor = StompHeaderAccessor.wrap(event.getMessage());
        String simpDestination = headerAccessor.getDestination();
        logger.debug("Subscribed to {}", simpDestination);

        if (WebSocketConfig.INTERNAL_ML_WORKER_CONFIG_TOPIC.equals(simpDestination))
            mlWorkerWSCommService.notifyMaxReplyPayloadLength(MLWorkerID.INTERNAL,
                applicationProperties.getMaxStompReplyMessagePayloadSize());

        if (WebSocketConfig.EXTERNAL_ML_WORKER_CONFIG_TOPIC.equals(simpDestination))
            mlWorkerWSCommService.notifyMaxReplyPayloadLength(MLWorkerID.EXTERNAL,
                applicationProperties.getMaxStompReplyMessagePayloadSize());
    }
}
