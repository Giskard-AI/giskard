package ai.giskard.config;

import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ApiKeyService;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.service.ml.MLWorkerWSService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.security.config.annotation.web.messaging.MessageSecurityMetadataSourceRegistry;
import org.springframework.security.config.annotation.web.socket.AbstractSecurityWebSocketMessageBrokerConfigurer;

@Configuration
@RequiredArgsConstructor
public class WebSocketSecurityConfig extends AbstractSecurityWebSocketMessageBrokerConfigurer {
    private final TokenProvider tokenProvider;
    private final LicenseService licenseService;
    private final MLWorkerWSService mlWorkerWSService;
    private final FileLocationService fileLocationService;
    private final ApiKeyService apiKeyService;

    @Override
    protected boolean sameOriginDisabled() {
        return true;
    }

    @Override
    protected void customizeClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(
            new WebSocketChannelInterceptor(tokenProvider, licenseService, mlWorkerWSService, fileLocationService, apiKeyService)
        );
    }

    @Override
    protected void configureInbound(MessageSecurityMetadataSourceRegistry messages) {
        // normally `.authenticated()` should've been used, but we need the connection to be authenticated at this point
        // since jwt token is sent as a CONNECT header it's too early to filter here and we do it in the preSend
        // interceptor
        messages.anyMessage().permitAll();
    }
}

