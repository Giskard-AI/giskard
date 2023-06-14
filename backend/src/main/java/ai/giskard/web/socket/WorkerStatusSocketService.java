package ai.giskard.web.socket;

import ai.giskard.service.ml.MLWorkerService;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.util.HashMap;
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
                simpMessagingTemplate.convertAndSend(
                    "/topic/worker-status",
                    new HashMap<String, Boolean>() {{
                        put("connected", mlWorkerService.isExternalWorkerConnected());
                    }}
                );
            }
        }, 0, 5000);
    }
}

