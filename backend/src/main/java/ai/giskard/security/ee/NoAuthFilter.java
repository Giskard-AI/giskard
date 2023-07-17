package ai.giskard.security.ee;

import ai.giskard.security.GiskardUser;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.GenericFilterBean;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import java.io.IOException;
import java.util.Collection;
import java.util.stream.Stream;

public class NoAuthFilter extends GenericFilterBean {

    /**
     * Generates a dummy authentication object that is admin.
     *
     * @return
     */
    public static Authentication getDummyAuthentication() {
        Collection<? extends GrantedAuthority> authorities = Stream.of("ROLE_ADMIN")
            .map(SimpleGrantedAuthority::new)
            .toList();

        GiskardUser principal = new GiskardUser(0L, "admin", "", authorities);

        return new UsernamePasswordAuthenticationToken(principal, "default", authorities);
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) throws IOException, ServletException {
        Authentication authentication = getDummyAuthentication();
        SecurityContextHolder.getContext().setAuthentication(authentication);
        chain.doFilter(request, response);
    }
}
