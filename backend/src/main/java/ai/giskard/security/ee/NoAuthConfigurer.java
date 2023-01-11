package ai.giskard.security.ee;

import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import org.springframework.security.config.annotation.SecurityConfigurerAdapter;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.DefaultSecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

public class NoAuthConfigurer extends SecurityConfigurerAdapter<DefaultSecurityFilterChain, HttpSecurity> {

    private final UserRepository userRepository;

    public NoAuthConfigurer(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public void configure(HttpSecurity http) {
        User admin = this.userRepository.getOneByLogin("admin");
        NoAuthFilter customFilter = new NoAuthFilter(admin.getId(), admin.getLogin());
        http.addFilterBefore(customFilter, UsernamePasswordAuthenticationFilter.class);
    }
}
