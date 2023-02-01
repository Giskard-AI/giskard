package ai.giskard.web.rest;

import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.GiskardUser;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.test.context.support.WithSecurityContext;
import org.springframework.security.test.context.support.WithSecurityContextFactory;
import org.springframework.util.Assert;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

@Target({ ElementType.METHOD, ElementType.TYPE })
@Retention(RetentionPolicy.RUNTIME)
@WithSecurityContext(factory = WithMockGiskardUser.Factory.class)
public @interface WithMockGiskardUser {

    long userId() default 1L;
    String username() default "admin";
    String[] roles() default { AuthoritiesConstants.ADMIN };

    class Factory implements WithSecurityContextFactory<WithMockGiskardUser> {

        @Override
        public SecurityContext createSecurityContext(WithMockGiskardUser annotation) {
            String username = annotation.username();
            Assert.hasLength(username, "value() must be non-empty String");

            List<SimpleGrantedAuthority> authorities = Arrays.stream(annotation.roles())
                .map(SimpleGrantedAuthority::new)
                .toList();

            UserDetails principal = new GiskardUser(annotation.userId(), username, username, true, true, true, true, authorities);

            Authentication authentication = new UsernamePasswordAuthenticationToken(principal, principal.getPassword(), principal.getAuthorities());
            SecurityContext context = SecurityContextHolder.createEmptyContext();
            context.setAuthentication(authentication);
            return context;
        }
    }
}
