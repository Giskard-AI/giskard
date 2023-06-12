package ai.giskard.config;

import com.corundumstudio.socketio.Configuration;
import com.corundumstudio.socketio.SocketIOServer;
import org.springframework.context.annotation.Bean;
import org.springframework.core.env.Environment;

import javax.annotation.PreDestroy;

@org.springframework.context.annotation.Configuration
public class SocketIOConfig {

    private SocketIOServer server;
    private final Environment env;

    public SocketIOConfig(Environment env) {
        this.env = env;
    }

    @Bean
    public SocketIOServer socketIOServer() {
        Configuration config = new Configuration();
        config.setHostname("localhost");
        String port = env.getProperty("server.port");
        if (port == null) {
            config.setPort(9000);
        } else {
            config.setPort(Integer.parseInt(port));
        }
        server = new SocketIOServer(config);
        server.start();
        return server;
    }

    @PreDestroy
    public void stopSocketIOServer() {
        if (server != null) {
            server.stop();
        }
    }
}
