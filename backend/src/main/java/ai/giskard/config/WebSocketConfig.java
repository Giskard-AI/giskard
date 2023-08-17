package ai.giskard.config;

import ai.giskard.ml.MLWorkerID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.socket.config.annotation.*;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletRequestWrapper;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Collections;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    public static final String ML_WORKER_TOPIC_PREFIX = "/ml-worker";
    public static final String ML_WORKER_ACTION_TOPIC = "action";
    public static final String ML_WORKER_CONFIG_TOPIC = "config";
    public static final String INTERNAL_ML_WORKER_TOPIC =
        String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, MLWorkerID.INTERNAL.toString(), ML_WORKER_ACTION_TOPIC);
    public static final String EXTERNAL_ML_WORKER_TOPIC =
        String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, MLWorkerID.EXTERNAL.toString(), ML_WORKER_ACTION_TOPIC);
    public static final String INTERNAL_ML_WORKER_CONFIG_TOPIC =
        String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, MLWorkerID.INTERNAL.toString(), ML_WORKER_CONFIG_TOPIC);
    public static final String EXTERNAL_ML_WORKER_CONFIG_TOPIC =
        String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, MLWorkerID.EXTERNAL.toString(), ML_WORKER_CONFIG_TOPIC);

    public static final String WEBSOCKET_ENDPOINT = "/websocket";

    // Another endpoint is needed to identify the previous version of Giskard server
    public static final String MLWORKER_WEBSOCKET_ENDPOINT = "/ml-worker";

    /**
     * For some reason when running on HuggingFace the connection header is set replacement "UPGRADE" instead of "Upgrade"
     * it causes websocket handshake replacement fail. This filter fixes the header.
     */
    @Component
    static class FixUpgradeHeadersFilter extends OncePerRequestFilter {
        private static final Logger log = LoggerFactory.getLogger(FixUpgradeHeadersFilter.class);

        private record HeaderReplacement(String original, String replacement) {
        }

        private static final Map<String, HeaderReplacement> HEADER_REPLACEMENTS = Map.of(
            "connection", new HeaderReplacement("UPGRADE", "Upgrade")
        );

        @Override
        protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

            final HttpServletRequestWrapper reqWrapper = new HttpServletRequestWrapper(request) {
                @Override
                public Enumeration<String> getHeaders(String name) {
                    String nameLowerCase = name.toLowerCase();
                    if ((WEBSOCKET_ENDPOINT.equals(request.getServletPath())  ||
                        MLWORKER_WEBSOCKET_ENDPOINT.equals(request.getServletPath())) &&
                        HEADER_REPLACEMENTS.containsKey(nameLowerCase) &&
                        HEADER_REPLACEMENTS.get(nameLowerCase).original.equals(super.getHeaders(nameLowerCase).nextElement())) {

                        String replacement = HEADER_REPLACEMENTS.get(nameLowerCase).replacement;
                        log.warn("Replacing header {} with {}", name, replacement);
                        return Collections.enumeration(Collections.singleton(replacement));
                    }
                    return super.getHeaders(name);
                }

                @Override
                public String getHeader(String name) {
                    String nameLowerCase = name.toLowerCase();
                    if ((WEBSOCKET_ENDPOINT.equals(request.getServletPath()) ||
                        MLWORKER_WEBSOCKET_ENDPOINT.equals(request.getServletPath())) &&
                        HEADER_REPLACEMENTS.containsKey(nameLowerCase) &&
                        HEADER_REPLACEMENTS.get(nameLowerCase).original.equals(super.getHeader(name))) {

                        String replacement = HEADER_REPLACEMENTS.get(nameLowerCase).replacement;
                        log.warn("Replacing header {} with {}", name, replacement);
                        return replacement;
                    }
                    return super.getHeader(name.toLowerCase());
                }
            };

            filterChain.doFilter(reqWrapper, response);
        }
    }


    public WebSocketConfig(ApplicationProperties applicationProperties) {
        this.applicationProperties = applicationProperties;
    }

    private final ApplicationProperties applicationProperties;

    @Override
    public void configureWebSocketTransport(WebSocketTransportRegistration registry) {
        // Allow to receive larger STOMP package (65535 bytes by default)
        registry.setMessageSizeLimit(applicationProperties.getMaxStompMessageSize());
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic", ML_WORKER_TOPIC_PREFIX);
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        CorsConfiguration config = applicationProperties.getCors();
        List<String> allowedOrigins = config.getAllowedOrigins();
        StompWebSocketEndpointRegistration endpoint = registry.addEndpoint(WEBSOCKET_ENDPOINT);
        if (!CollectionUtils.isEmpty(allowedOrigins)) {
            endpoint.setAllowedOrigins(allowedOrigins.toArray(String[]::new));
        }
        StompWebSocketEndpointRegistration mlWorkerEndpoint = registry.addEndpoint(MLWORKER_WEBSOCKET_ENDPOINT);
        if (!CollectionUtils.isEmpty(allowedOrigins)) {
            mlWorkerEndpoint.setAllowedOrigins(allowedOrigins.toArray(String[]::new));
        }
    }
}
