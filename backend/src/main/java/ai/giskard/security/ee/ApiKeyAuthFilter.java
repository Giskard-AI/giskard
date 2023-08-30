package ai.giskard.security.ee;

import ai.giskard.domain.ApiKey;
import ai.giskard.domain.Role;
import ai.giskard.security.GiskardUser;
import ai.giskard.service.ApiKeyService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.GenericFilterBean;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Optional;

import static ai.giskard.security.AuthoritiesConstants.API;

@RequiredArgsConstructor
public class ApiKeyAuthFilter extends GenericFilterBean {
    private final ApiKeyService apiKeyService;

    public static Authentication getAuthentication(ApiKey apiKey) {
        Collection<SimpleGrantedAuthority> authorities = new ArrayList<>();
        authorities.add(new SimpleGrantedAuthority(API));
        for (Role role : apiKey.getUser().getRoles()) {
            authorities.add(new SimpleGrantedAuthority(role.getName()));
        }

        GiskardUser principal = new GiskardUser(apiKey.getUser().getId(), apiKey.getUser().getLogin(), "", authorities);

        return new UsernamePasswordAuthenticationToken(principal, apiKey.getKey(), authorities);
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        String apiKey = ((HttpServletRequest) request).getHeader(HttpHeaders.AUTHORIZATION).substring(7);
        Optional<ApiKey> foundKey = apiKeyService.getKey(apiKey);
        foundKey.ifPresent(key -> SecurityContextHolder.getContext().setAuthentication(getAuthentication(key)));
        chain.doFilter(request, response);
    }
}
