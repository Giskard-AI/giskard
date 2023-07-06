package ai.giskard.ml;

import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.ApplicationListener;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.SessionDisconnectEvent;

@Component
@RequiredArgsConstructor
public class WSDisconnectEventListener implements ApplicationListener<SessionDisconnectEvent> {
    private final Logger logger = LoggerFactory.getLogger(WSDisconnectEventListener.class.getName());

    private final MLWorkerWSService mlWorkerWSService;

    @Override
    public void onApplicationEvent(SessionDisconnectEvent event) {
        logger.debug("Session " + event.getSessionId() + " closed");

        if (mlWorkerWSService.removeWorker(event.getSessionId())) {
            logger.debug("Worker " + event.getSessionId() + " removed");
        } else {
            logger.debug("Session " + event.getSessionId() + " is not a worker nor a potential worker");
        }
    }
}
