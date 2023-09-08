package ai.giskard.security.ee;

import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ApiKeyService;
import ai.giskard.service.ee.LicenseService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.config.annotation.SecurityConfigurerAdapter;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.DefaultSecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@RequiredArgsConstructor
public class GiskardAuthConfigurer extends SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity> {
    private final LicenseService licenseService;
    private final ApiKeyService apiKeyService;
    private final TokenProvider tokenProvider;


    @Override
    public void configure(HttpSecurity http) {
        GiskardAuthFilter customFilter = new GiskardAuthFilter(licenseService, apiKeyService, tokenProvider);
        http.addFilterBefore(customFilter, UsernamePasswordAuthenticationFilter.class);

    }
}
