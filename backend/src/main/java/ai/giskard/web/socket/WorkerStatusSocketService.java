package ai.giskard.web.socket;

import ai.giskard.event.UpdateWorkerStatusEvent;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.service.ml.MLWorkerWSService;
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

    private final MLWorkerWSService mlWorkerWSService;
    private final SimpMessagingTemplate simpMessagingTemplate;

    @EventListener
    public void handleSessionSubscribeEvent(SessionSubscribeEvent event) {
        sendCurrentStatus();
    }

    @EventListener()
    public void handleWorkerStatusChangeEvent(UpdateWorkerStatusEvent event) {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", event.isConnected());
        sendData(data);
    }


    public void sendCurrentStatus() {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL));
        sendData(data);
    }

    private void sendData(Map<String, Boolean> data) {
        simpMessagingTemplate.convertAndSend(
                "/topic/worker-status",
                data);
    }
}
