package ai.giskard.web.socket;

import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.ml.MLWorkerService;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

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
                data.put("connected",
                    // HF Space uses internal worker that always connected
                    mlWorkerService.isExternalWorkerConnected() || GeneralSettingsService.isRunningInHFSpaces
                );

                simpMessagingTemplate.convertAndSend(
                        "/topic/worker-status",
                        data);
            }
        }, 0, 5000);
    }
}
