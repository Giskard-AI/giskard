package ai.giskard.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.util.CollectionUtils;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketTransportRegistration;
import tech.jhipster.config.JHipsterProperties;

import java.util.List;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final JHipsterProperties jHipsterProperties;

    public WebSocketConfig(JHipsterProperties jHipsterProperties) {
        this.jHipsterProperties = jHipsterProperties;
    }

    @Override
    public void configureWebSocketTransport(WebSocketTransportRegistration registry) {
        // Allow to receive larger STOMP package (65535 bytes by default)
        registry.setMessageSizeLimit(1024 * 1024);
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic", "/ml-worker");
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        CorsConfiguration config = jHipsterProperties.getCors();
        List<String> allowedOrigins = config.getAllowedOrigins();

        if (!CollectionUtils.isEmpty(allowedOrigins)) {
            registry
                .addEndpoint("/websocket")
                .setAllowedOrigins(allowedOrigins.toArray(String[]::new));
        } else {
            registry.addEndpoint("/websocket");
        }
    }
}
