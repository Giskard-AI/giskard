package ai.giskard.web.socket;

import ai.giskard.event.UpdateWorkerStatusEvent;
import ai.giskard.service.ml.MLWorkerService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.messaging.SessionSubscribeEvent;
import java.util.HashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class WorkerStatusSocketService {

    private final MLWorkerService mlWorkerService;
    private final SimpMessagingTemplate simpMessagingTemplate;

    @EventListener
    public void handleSessionSubscribeEvent(SessionSubscribeEvent event) {
        sendCurrentStatus();
    }

    @EventListener
    public void handleUpdateWorkerStatusEvent(UpdateWorkerStatusEvent event) {
        sendCurrentStatus();
    }

    public void sendCurrentStatus() {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", mlWorkerService.isExternalWorkerConnected());

        simpMessagingTemplate.convertAndSend(
                "/topic/worker-status",
                data);
    }
}
