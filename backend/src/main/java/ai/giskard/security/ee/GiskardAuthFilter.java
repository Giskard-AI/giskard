package ai.giskard.security.ee;

import ai.giskard.domain.ApiKey;
import ai.giskard.security.ee.jwt.JWTFilter;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ApiKeyService;
import ai.giskard.service.ee.FeatureFlag;
import ai.giskard.service.ee.LicenseService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.web.filter.GenericFilterBean;

import java.io.IOException;


/**
 * This filter is applied for every request and will check for authentication.
 * It will check if authentication is enabled on the instance and pick between the admin-by-default filter or the JWT filter
 */
public class GiskardAuthFilter extends GenericFilterBean {

    private final LicenseService licenseService;

    private final JWTFilter jwtFilter;
    private final NoAuthFilter noAuthFilter;
    private final ApiKeyAuthFilter apiKeyAuthFilter;
    private final NoLicenseAuthFilter noLicenseAuthFilter;

    public GiskardAuthFilter(LicenseService licenseService, ApiKeyService apiKeyService, TokenProvider tokenProvider) {
        this.licenseService = licenseService;

        this.jwtFilter = new JWTFilter(tokenProvider);
        this.noAuthFilter = new NoAuthFilter();
        this.noLicenseAuthFilter = new NoLicenseAuthFilter();
        this.apiKeyAuthFilter = new ApiKeyAuthFilter(apiKeyService);
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        HttpServletRequest httpServletRequest = (HttpServletRequest) request;
        if (!this.licenseService.getCurrentLicense().isActive()) {
            this.noLicenseAuthFilter.doFilter(request, response, chain);
        } else if (this.licenseService.hasFeature(FeatureFlag.AUTH) || httpServletRequest.getHeader(HttpHeaders.AUTHORIZATION) != null) {
            String authHeader = httpServletRequest.getHeader(HttpHeaders.AUTHORIZATION);
            if (authHeader != null) {
                // remove the "Bearer " prefix
                authHeader = authHeader.substring(7);
            }
            // even if AUTH isn't enabled (no multi-user support), check the token for python client/ML Worker requests
            if (ApiKey.doesStringLookLikeApiKey(authHeader)) {
                this.apiKeyAuthFilter.doFilter(request, response, chain);
            } else {
                this.jwtFilter.doFilter(request, response, chain);
            }
        } else {
            this.noAuthFilter.doFilter(request, response, chain);
        }
    }
}
