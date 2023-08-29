package ai.giskard.config;

import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.ee.GiskardAuthConfigurer;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.ee.LicenseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.SecurityConfigurerAdapter;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.annotation.web.configurers.HeadersConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.DefaultSecurityFilterChain;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.header.writers.ReferrerPolicyHeaderWriter;

import static ai.giskard.config.WebSocketConfig.MLWORKER_WEBSOCKET_ENDPOINT;
import static ai.giskard.config.WebSocketConfig.WEBSOCKET_ENDPOINT;
import static org.springframework.security.config.Customizer.withDefaults;
import static org.springframework.security.web.util.matcher.AntPathRequestMatcher.antMatcher;

@EnableWebSecurity
@EnableMethodSecurity(securedEnabled = true)
@Configuration
public class SecurityConfiguration {
    @Autowired
    private TokenProvider tokenProvider;
    @Autowired
    private LicenseService licenseService;


    public static final String GISKARD_API_ENDPOINTS = "/api/**";
    public static final String GISKARD_HF_GALLERY_SPACE_ID = "giskardai/giskard";
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        // Deny requests other than GET for Giskard gallery repo on Hugging Face Spaces
        if (GeneralSettingsService.hfSpaceId.equals(GISKARD_HF_GALLERY_SPACE_ID)) {
            http.authorizeHttpRequests(registry ->
                // For any allowed requests with authorization, put them here
                registry.requestMatchers(
                    antMatcher("/api/v2/dataset/**/rows"),                  // Permit shuffle dataset
                    antMatcher("/api/v2/project/**/datasets/**/process"),   // Permit dataset processing
                    antMatcher("/api/v2/models/**/predict"),                // Permit model run
                    antMatcher("/api/v2/models/**/explain/**"),             // Permit model explain
                    antMatcher("/api/v2/models/models/explain-text/**")     // Permit model explain text
                ).authenticated()
            ).authorizeHttpRequests(authorizeHttpRequests ->
                // Deny all other APIs
                authorizeHttpRequests.requestMatchers(
                    antMatcher(HttpMethod.POST, GISKARD_API_ENDPOINTS),
                    antMatcher(HttpMethod.PUT, GISKARD_API_ENDPOINTS),
                    antMatcher(HttpMethod.DELETE, GISKARD_API_ENDPOINTS)
                ).hasAuthority(AuthoritiesConstants.HF_SUPERUSER)
            );  // Needs HF Superuser permission, but no one has it
        }

        http
            .cors(withDefaults())
            .csrf(AbstractHttpConfigurer::disable)
            .headers(conf -> conf
                .referrerPolicy(referrerPolicyConfig -> referrerPolicyConfig.policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))
                .frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin)
            ).sessionManagement(conf -> conf.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers(
                    antMatcher(WEBSOCKET_ENDPOINT),
                    antMatcher(MLWORKER_WEBSOCKET_ENDPOINT),
                    antMatcher(HttpMethod.OPTIONS, "/**"),
                    antMatcher("/swagger-ui/**"),
                    antMatcher("/v3/api-docs/**"),
                    antMatcher("/test/**"),
                    antMatcher("/api/v2/dev/**"),
                    antMatcher("/api/v2/settings/license"),
                    antMatcher("/api/v2/settings"),
                    antMatcher("/api/v2/setup"),
                    antMatcher("/api/v2/ee/license"),
                    antMatcher("/api/v2/authenticate"),
                    antMatcher("/api/v2/register"),
                    antMatcher("/api/v2/register"),
                    antMatcher("/api/v2/activate"),
                    antMatcher("/api/v2/account/password-recovery"),
                    antMatcher("/api/v2/account/reset-password"),
                    antMatcher("/management/health"),
                    antMatcher("/management/health/**"),
                    antMatcher("/management/info"),
                    antMatcher("/management/prometheus")
                ).permitAll()
                .requestMatchers(
                    antMatcher("/api/admin/**"),
                    antMatcher("/management/**")
                ).hasAuthority(AuthoritiesConstants.ADMIN)
                .requestMatchers(antMatcher("/api/v2/settings/ml-worker-connect")).hasAuthority(AuthoritiesConstants.API)
                .requestMatchers(antMatcher(GISKARD_API_ENDPOINTS)).authenticated()
            )
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .apply(securityConfigurerAdapter());
        return http.build();
    }


    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    private SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity> securityConfigurerAdapter() {
        return new GiskardAuthConfigurer(licenseService, tokenProvider);
    }
}
