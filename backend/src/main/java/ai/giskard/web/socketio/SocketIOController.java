package ai.giskard.web.socketio;

import ai.giskard.service.ml.MLWorkerService;
import org.springframework.stereotype.Controller;
import com.corundumstudio.socketio.SocketIOServer;
import javax.annotation.PostConstruct;
import java.util.HashMap;
import java.util.Timer;
import java.util.TimerTask;

@Controller
public class SocketIOController {

    private final SocketIOServer socketServer;
    private final MLWorkerService mlWorkerService;


    public SocketIOController(SocketIOServer socketServer, MLWorkerService mlWorkerService) {
        this.socketServer = socketServer;
        this.mlWorkerService = mlWorkerService;
    }


    @PostConstruct
    public void init() {
        Timer timer = new Timer();
        timer.schedule(new TimerTask() {
            @Override
            public void run() {
                socketServer.getBroadcastOperations().sendEvent("worker-status",
                    new HashMap<String, Boolean>() {{
                        put("connected", mlWorkerService.isExternalWorkerConnected());
                    }}
                );
            }
        }, 0, 5000);
    }
}

