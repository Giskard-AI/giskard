package ai.giskard.config;

import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.ee.GiskardAuthConfigurer;
import ai.giskard.security.ee.jwt.TokenProvider;
import ai.giskard.service.ee.LicenseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.SecurityConfigurerAdapter;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityCustomizer;
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


    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .cors(withDefaults())
            .csrf(AbstractHttpConfigurer::disable)
            .headers(conf -> conf
                .referrerPolicy(referrerPolicyConfig -> referrerPolicyConfig.policy(ReferrerPolicyHeaderWriter.ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))
                .frameOptions(HeadersConfigurer.FrameOptionsConfig::sameOrigin)
            ).sessionManagement(conf -> conf.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers(antMatcher("/api/v2/dev/**")).permitAll()
                .requestMatchers(antMatcher("/api/v2/settings/license")).permitAll()
                .requestMatchers(antMatcher("/api/v2/settings/ml-worker-connect")).hasAuthority(AuthoritiesConstants.API)
                .requestMatchers(antMatcher("/api/v2/settings")).permitAll()
                .requestMatchers(antMatcher("/api/v2/setup")).permitAll()
                .requestMatchers(antMatcher("/api/v2/ee/license")).permitAll()
                .requestMatchers(antMatcher("/api/v2/authenticate")).permitAll()
                .requestMatchers(antMatcher("/api/v2/register")).permitAll()
                .requestMatchers(antMatcher("/api/v2/register")).permitAll()
                .requestMatchers(antMatcher("/api/v2/activate")).permitAll()
                .requestMatchers(antMatcher("/api/v2/account/password-recovery")).permitAll()
                .requestMatchers(antMatcher("/api/v2/account/reset-password")).permitAll()
                .requestMatchers(antMatcher("/api/admin/**")).hasAuthority(AuthoritiesConstants.ADMIN)
                .requestMatchers(antMatcher("/api/**")).authenticated()
                .requestMatchers(antMatcher("/management/health")).permitAll()
                .requestMatchers(antMatcher("/management/health/**")).permitAll()
                .requestMatchers(antMatcher("/management/info")).permitAll()
                .requestMatchers(antMatcher("/management/prometheus")).permitAll()
                .requestMatchers(antMatcher("/management/**")).hasAuthority(AuthoritiesConstants.ADMIN)
            )
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .apply(securityConfigurerAdapter());
        return http.build();
    }

    @Bean
    public WebSecurityCustomizer webSecurityCustomizer() {
        return web -> web.ignoring()
            .requestMatchers(antMatcher(WEBSOCKET_ENDPOINT))
            .requestMatchers(antMatcher(MLWORKER_WEBSOCKET_ENDPOINT))
            .requestMatchers(antMatcher(HttpMethod.OPTIONS, "/**"))
            .requestMatchers(antMatcher("/swagger-ui/**"))
            .requestMatchers(antMatcher("/test/**"));
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    private SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity> securityConfigurerAdapter() {
        return new GiskardAuthConfigurer(licenseService, tokenProvider);
    }
}
