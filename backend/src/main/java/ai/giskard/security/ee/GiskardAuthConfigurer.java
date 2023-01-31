package ai.giskard.security.ee;

import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ee.LicenseService;
import org.springframework.security.config.annotation.SecurityConfigurerAdapter;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.DefaultSecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

public class GiskardAuthConfigurer extends SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity> {
    private final LicenseService licenseService;
    private final TokenProvider tokenProvider;

    public GiskardAuthConfigurer(LicenseService licenseService, TokenProvider tokenProvider) {
        this.licenseService = licenseService;
        this.tokenProvider = tokenProvider;
    }

    @Override
    public void configure(HttpSecurity http) {
        GiskardAuthFilter customFilter = new GiskardAuthFilter(licenseService, tokenProvider);
        http.addFilterBefore(customFilter, UsernamePasswordAuthenticationFilter.class);
    }
}
