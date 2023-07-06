package ai.giskard.web.socket;

import ai.giskard.service.ml.MLWorkerService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.messaging.SessionSubscribeEvent;

import javax.annotation.PostConstruct;
import java.util.HashMap;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

@Service
@RequiredArgsConstructor
public class WorkerStatusSocketService {

    private final MLWorkerService mlWorkerService;
    private final SimpMessagingTemplate simpMessagingTemplate;

    @PostConstruct
    public void init() {
        Timer timer = new Timer();
        timer.schedule(new TimerTask() {
            @Override
            public void run() {
                Map<String, Boolean> data = new HashMap<>();
                data.put("connected", mlWorkerService.isExternalWorkerConnected());

                simpMessagingTemplate.convertAndSend(
                        "/topic/worker-status",
                        data);
            }
        }, 0, 60000);
    }

    @EventListener
    public void handleSessionSubscribeEvent(SessionSubscribeEvent event) {
        Map<String, Boolean> data = new HashMap<>();
        data.put("connected", mlWorkerService.isExternalWorkerConnected());

        simpMessagingTemplate.convertAndSend(
                "/topic/worker-status",
                data);
    }
}
