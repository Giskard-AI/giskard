package ai.giskard.config;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.ee.FeatureFlag;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.config.annotation.web.messaging.MessageSecurityMetadataSourceRegistry;
import org.springframework.security.config.annotation.web.socket.AbstractSecurityWebSocketMessageBrokerConfigurer;
import org.springframework.security.core.Authentication;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Objects;

import static ai.giskard.security.ee.NoAuthFilter.getDummyAuthentication;

@Configuration
@RequiredArgsConstructor
public class WebSocketSecurityConfig extends AbstractSecurityWebSocketMessageBrokerConfigurer {
    private final Logger log = LoggerFactory.getLogger(WebSocketSecurityConfig.class);

    private final TokenProvider tokenProvider;
    private final LicenseService licenseService;
    private final MLWorkerWSService mlWorkerWSService;
    private final FileLocationService fileLocationService;

    @Override
    protected boolean sameOriginDisabled() {
        return true;
    }

    @Override
    protected void customizeClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(new ChannelInterceptor() {
            @Override
            public Message<?> preSend(Message<?> message, MessageChannel channel) {
                StompHeaderAccessor accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
                if (accessor == null){
                    throw new AccessDeniedException("Failed to read STOMP headers");
                }
                if (StompCommand.CONNECT.equals(accessor.getCommand())) {
                    log.debug("Session {} CONNECT", accessor.getSessionId());
                    // Check if an internal worker trying to connect
                    List<String> internalTokenHeaders = accessor.getNativeHeader("token");
                    if (internalTokenHeaders != null && !internalTokenHeaders.isEmpty()
                        && StringUtils.hasText(internalTokenHeaders.get(0))) {
                        // Validate the token
                        try {
                            String token = Files.readString(Paths.get(fileLocationService.giskardHome().toString(), "run", "internal-ml-worker"));
                            if (StringUtils.hasText(token) && token.equals(internalTokenHeaders.get(0)) &&
                                mlWorkerWSService.prepareInternalWorker(Objects.requireNonNull(accessor.getSessionId()))) {
                                log.debug("Potential internal worker connected \"{}\"", accessor.getSessionId());
                                return message;
                            }
                        } catch (IOException e) {
                            log.warn("Unable to load token for the internal ML Worker");
                        }
                    }

                    if (licenseService.hasFeature(FeatureFlag.AUTH)) {
                        List<String> jwtHeaders = accessor.getNativeHeader("jwt");
                        if (jwtHeaders == null || jwtHeaders.isEmpty() || !StringUtils.hasText(jwtHeaders.get(0))) {
                            log.warn("Missing JWT token");
                            throw new AccessDeniedException("Missing JWT token");
                        } else if (!tokenProvider.validateToken(jwtHeaders.get(0))) {
                            log.warn("Invalid JWT token");
                            throw new AccessDeniedException("Invalid JWT token");
                        }
                        Authentication authentication = tokenProvider.getAuthentication(jwtHeaders.get(0));
                        accessor.setUser(authentication);
                    } else {
                        accessor.setUser(getDummyAuthentication());
                    }

                }

                if (StompCommand.SUBSCRIBE.equals(accessor.getCommand())) {
                    String destination = accessor.getDestination();
                    if (destination == null)
                        throw new AccessDeniedException("Cannot find available worker");
                    if (!destination.startsWith("/ml-worker/"))
                        return message; // By-pass the other subscriptions

                    // Check MLWorker-related topics
                    if (destination.equals(WebSocketConfig.INTERNAL_ML_WORKER_TOPIC)) {
                        if (mlWorkerWSService.associateWorker(MLWorkerID.INTERNAL.toString(),
                            Objects.requireNonNull(accessor.getSessionId()))) {
                            return message;
                        }
                    } else if (destination.equals(WebSocketConfig.EXTERNAL_ML_WORKER_TOPIC)) {
                        if (mlWorkerWSService.associateWorker(MLWorkerID.EXTERNAL.toString(),
                            Objects.requireNonNull(accessor.getSessionId()))) {
                            return message;
                        }
                    }
                    if (destination.equals(WebSocketConfig.INTERNAL_ML_WORKER_CONFIG_TOPIC) ||
                        destination.equals(WebSocketConfig.EXTERNAL_ML_WORKER_CONFIG_TOPIC))
                        return message;

                    throw new AccessDeniedException("Cannot find available worker");
                }

                return message;
            }
        });
    }

    @Override
    protected void configureInbound(MessageSecurityMetadataSourceRegistry messages) {
        // normally `.authenticated()` should've been used, but we need the connection to be authenticated at this point
        // since jwt token is sent as a CONNECT header it's too early to filter here and we do it in the preSend
        // interceptor
        messages.anyMessage().permitAll();
    }
}

