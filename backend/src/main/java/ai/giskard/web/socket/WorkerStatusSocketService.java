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

    @EventListener(condition = "#event.isConnected == true")
    public void handleWorkerConnectedEvent(UpdateWorkerStatusEvent event) {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", true);
        sendData(data);
    }

    @EventListener(condition = "#event.isConnected == false")
    public void handleWorkerDisconnectedEvent(UpdateWorkerStatusEvent event) {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", false);
        sendData(data);
    }

    public void sendCurrentStatus() {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", mlWorkerService.isExternalWorkerConnected());

        sendData(data);
    }

    private void sendData(Map<String, Boolean> data) {
        simpMessagingTemplate.convertAndSend(
                "/topic/worker-status",
                data);
    }
}
