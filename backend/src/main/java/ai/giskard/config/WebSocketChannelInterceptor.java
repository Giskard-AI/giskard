package ai.giskard.config;

import ai.giskard.domain.ApiKey;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.security.ee.ApiKeyAuthFilter;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ApiKeyService;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.ee.FeatureFlag;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Objects;

import static ai.giskard.security.ee.NoAuthFilter.getDummyAuthentication;

@RequiredArgsConstructor
public class WebSocketChannelInterceptor implements ChannelInterceptor {
    private final Logger log = LoggerFactory.getLogger(WebSocketChannelInterceptor.class);

    private final TokenProvider tokenProvider;
    private final LicenseService licenseService;
    private final MLWorkerWSService mlWorkerWSService;
    private final FileLocationService fileLocationService;
    private final ApiKeyService apiKeyService;

    private boolean isValidateTokenForInternalMLWorker(List<String> internalTokenHeaders) {
        if (internalTokenHeaders != null && !internalTokenHeaders.isEmpty()
            && StringUtils.hasText(internalTokenHeaders.get(0))) {
            // Validate the token
            try {
                String token = Files.readString(Paths.get(fileLocationService.giskardHome().toString(), "run", "internal-ml-worker"));
                if (StringUtils.hasText(token) && token.equals(internalTokenHeaders.get(0))) {
                    return true;
                }
            } catch (IOException e) {
                log.warn("Unable to load token for the internal ML Worker");
            }
        }
        return false;
    }

    private Message<?> processConnectMessage(Message<?> message, StompHeaderAccessor accessor) {
        log.debug("Session {} CONNECT", accessor.getSessionId());
        // Check if an internal worker trying to connect
        List<String> internalTokenHeaders = accessor.getNativeHeader("token");
        if (isValidateTokenForInternalMLWorker(internalTokenHeaders)) {
            boolean couldBeInternalWorker =
                mlWorkerWSService.prepareInternalWorker(Objects.requireNonNull(accessor.getSessionId()));
            if (couldBeInternalWorker) {
                log.debug("Potential internal worker connected \"{}\"", accessor.getSessionId());
                return message;
            }
        }

        if (licenseService.hasFeature(FeatureFlag.AUTH)) {
            List<String> apiKeyHeaders = accessor.getNativeHeader("api-key");
            List<String> jwtHeaders = accessor.getNativeHeader("jwt");
            if (jwtHeaders != null) {
                // Websocket connection is coming from the UI
                if (jwtHeaders.isEmpty() || !StringUtils.hasText(jwtHeaders.get(0))) {
                    log.warn("Missing JWT token");
                    throw new AccessDeniedException("Missing JWT token");
                } else if (!tokenProvider.validateToken(jwtHeaders.get(0))) {
                    log.warn("Invalid JWT token");
                    throw new AccessDeniedException("Invalid JWT token");
                }
                Authentication authentication = tokenProvider.getAuthentication(jwtHeaders.get(0));
                accessor.setUser(authentication);
            } else if (apiKeyHeaders != null) {
                // Websocket connection is coming from the ML Worker
                if (apiKeyHeaders.isEmpty() || !StringUtils.hasText(apiKeyHeaders.get(0))) {
                    log.warn("Missing API key header");
                    throw new AccessDeniedException("Missing API key");
                }
                String apiKey = apiKeyHeaders.get(0);
                if (!ApiKey.doesStringLookLikeApiKey(apiKey) || apiKeyService.getKey(apiKey).isEmpty()) {
                    log.warn("Invalid API key");
                    throw new AccessDeniedException("Invalid API key");
                }
                Authentication authentication = ApiKeyAuthFilter.getAuthentication(apiKeyService.getKey(apiKey).orElseThrow());
                accessor.setUser(authentication);
            }
        } else {
            accessor.setUser(getDummyAuthentication());
        }

        return message;
    }

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null){
            throw new AccessDeniedException("Failed to read STOMP headers");
        } else if (StompCommand.CONNECT.equals(accessor.getCommand())) {
            return processConnectMessage(message, accessor);
        } else if (StompCommand.SUBSCRIBE.equals(accessor.getCommand())) {
            return processSubscribeMessage(message, accessor);
        }
        return message;
    }

    private Message<?> processSubscribeMessage(Message<?> message, StompHeaderAccessor accessor) {
        String destination = accessor.getDestination();
        if (destination == null)
            throw new AccessDeniedException("Cannot find available worker");
        if (!destination.startsWith("/ml-worker/"))
            return message; // By-pass the other subscriptions

        // Check MLWorker-related topics
        boolean associated = false;
        if (destination.equals(WebSocketConfig.INTERNAL_ML_WORKER_TOPIC)) {
            associated = mlWorkerWSService.associateWorker(MLWorkerID.INTERNAL.toString(),
                Objects.requireNonNull(accessor.getSessionId()));
        } else if (destination.equals(WebSocketConfig.EXTERNAL_ML_WORKER_TOPIC)) {
            associated = mlWorkerWSService.associateWorker(MLWorkerID.EXTERNAL.toString(),
                Objects.requireNonNull(accessor.getSessionId()));
        }
        if (associated ||   // ML Worker association success
            destination.equals(WebSocketConfig.INTERNAL_ML_WORKER_CONFIG_TOPIC) ||
            destination.equals(WebSocketConfig.EXTERNAL_ML_WORKER_CONFIG_TOPIC))
            return message;

        throw new AccessDeniedException("Cannot find available worker");
    }
}
