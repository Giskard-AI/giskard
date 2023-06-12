package ai.giskard.web.socketio;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RestController;
import com.corundumstudio.socketio.SocketIOServer;
import javax.annotation.PostConstruct;
import java.util.Timer;
import java.util.TimerTask;


@RestController
public class SocketIOController {

    @Autowired
    private SocketIOServer socketServer;

    public SocketIOController(SocketIOServer socketServer) {
        this.socketServer = socketServer;
    }


    @PostConstruct
    public void init() {
        Timer timer = new Timer();
        timer.schedule(new TimerTask() {
            @Override
            public void run() {
                socketServer.getBroadcastOperations().sendEvent("worker-status", "test");
            }
        }, 0, 5000);
    }
}

