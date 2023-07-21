package ai.giskard.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.StompWebSocketEndpointRegistration;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;
import tech.jhipster.config.JHipsterProperties;

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

    public static final String WEBSOCKET_ENDPOINT = "/websocket";

    /**
     * For some reason when running on HuggingFace the connection header is set replacement "UPGRADE" instead of "Upgrade"
     * it causes websocket handshake replacement fail. This filter fixes the header.
     */
    @Component
    static class FixUpgradeHeadersFilter extends OncePerRequestFilter {
        private static final Logger log = LoggerFactory.getLogger(FixUpgradeHeadersFilter.class);

        private record HeaderReplacement(String original, String replacement) {}

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
                    if (WEBSOCKET_ENDPOINT.equals(request.getServletPath()) &&
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
                    if (WEBSOCKET_ENDPOINT.equals(request.getServletPath()) &&
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
        List<String> allowedOrigins = config.getAllowedOrigins();
        StompWebSocketEndpointRegistration endpoint = registry.addEndpoint(WEBSOCKET_ENDPOINT);
        if (!CollectionUtils.isEmpty(allowedOrigins)) {
            endpoint.setAllowedOrigins(allowedOrigins.toArray(String[]::new));
        }
    }
}
