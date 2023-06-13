package ai.giskard.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.util.CollectionUtils;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;
import tech.jhipster.config.JHipsterProperties;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final JHipsterProperties jHipsterProperties;

    public WebSocketConfig(JHipsterProperties jHipsterProperties) {
        this.jHipsterProperties = jHipsterProperties;
    }


    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic");
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        CorsConfiguration config = jHipsterProperties.getCors();

        if (!CollectionUtils.isEmpty(config.getAllowedOrigins()) || !CollectionUtils.isEmpty(config.getAllowedOriginPatterns())) {
            registry.addEndpoint("/websocket")
                .setAllowedOrigins(config.getAllowedOrigins().toArray(String[]::new));
        } else {
            registry.addEndpoint("/websocket");
        }
    }
}
