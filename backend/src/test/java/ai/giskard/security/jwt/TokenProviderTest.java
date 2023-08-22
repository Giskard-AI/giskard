package ai.giskard.security.jwt;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.management.SecurityMetersService;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.ee.jwt.TokenProvider;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.assertj.core.data.Offset;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

import static ai.giskard.security.jwt.JWTFilterTest.createAuthentication;
import static org.assertj.core.api.Assertions.assertThat;

class TokenProviderTest {

    private static final long ONE_MINUTE = 60000;
    private static final long DAYS_90 = (long) 90 * 24 * 60 * 60 * 1000;

    private Key key;
    private TokenProvider tokenProvider;

    @BeforeEach
    public void setup() {
        ApplicationProperties applicationProperties = new ApplicationProperties();

        String base64Secret = "fd54a45s65fds737b9aafcb3412e07ed99b267f33413274720ddbb7f6c5e64e9f14075f2d7ed041592f0b7657baf8"; //ggignore
        applicationProperties.setBase64JwtSecretKey(base64Secret);
        SecurityMetersService securityMetersService = new SecurityMetersService(new SimpleMeterRegistry());

        tokenProvider = new TokenProvider(applicationProperties, securityMetersService);
        key = Keys.hmacShaKeyFor(Decoders.BASE64.decode(base64Secret));

        ReflectionTestUtils.setField(tokenProvider, "key", key);
        ReflectionTestUtils.setField(tokenProvider, "tokenValidityInMilliseconds", ONE_MINUTE);
        ReflectionTestUtils.setField(tokenProvider, "apiTokenValidityInMilliseconds", DAYS_90);
    }

    @Test
    void testReturnFalseWhenJWThasInvalidSignature() {
        boolean isTokenValid = tokenProvider.validateToken(createTokenWithDifferentSignature());

        assertThat(isTokenValid).isFalse();
    }

    @Test
    void testReturnFalseWhenJWTisMalformed() {
        Authentication authentication = createAuthentication(AuthoritiesConstants.AITESTER);
        String token = tokenProvider.createToken(authentication, false).getToken();
        String invalidToken = token.substring(1);
        boolean isTokenValid = tokenProvider.validateToken(invalidToken);

        assertThat(isTokenValid).isFalse();
    }

    @Test
    void testReturnFalseWhenJWTisExpired() {
        ReflectionTestUtils.setField(tokenProvider, "tokenValidityInMilliseconds", -ONE_MINUTE);

        Authentication authentication = createAuthentication(AuthoritiesConstants.AITESTER);
        String token = tokenProvider.createToken(authentication, false).getToken();
        Assertions.assertThrows(ExpiredJwtException.class, () -> {
            tokenProvider.validateToken(token);
        });
    }

    @Test
    void testReturnFalseWhenJWTisUnsupported() {
        String unsupportedToken = createUnsupportedToken();

        boolean isTokenValid = tokenProvider.validateToken(unsupportedToken);

        assertThat(isTokenValid).isFalse();
    }

    @Test
    void testReturnFalseWhenJWTisInvalid() {
        boolean isTokenValid = tokenProvider.validateToken("");

        assertThat(isTokenValid).isFalse();
    }

    @Test
    void testAPIauthToken() {
        Instant tokenAcquiryDate = (new Date()).toInstant();
        String token = tokenProvider.createAPIaccessToken(createAuthentication(AuthoritiesConstants.AITESTER)).getToken();

        JwtParser jwtParser = Jwts.parserBuilder().setSigningKey(key).build();
        Claims claims = jwtParser.parseClaimsJws(token).getBody();
        assertThat(claims.getSubject()).isEqualTo("test-user");
        long tokenValidityDays = Duration.between(tokenAcquiryDate, claims.getExpiration().toInstant()).toMillis();

        assertThat(tokenValidityDays).isCloseTo(DAYS_90, Offset.offset((long) 1000));
    }

    @Test
    void testKeyIsSetFromSecretWhenSecretIsNotEmpty() {
        final String secret = "NwskoUmKHZtzGRKJKVjsJF7BtQMMxNWi"; //ggignore
        ApplicationProperties applicationProperties = new ApplicationProperties();
        applicationProperties.setJwtSecretKey(secret);

        SecurityMetersService securityMetersService = new SecurityMetersService(new SimpleMeterRegistry());

        TokenProvider tokenProvider = new TokenProvider(applicationProperties, securityMetersService);

        Key key = (Key) ReflectionTestUtils.getField(tokenProvider, "key");
        assertThat(key).isNotNull().isEqualTo(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void testKeyIsSetFromBase64SecretWhenSecretIsEmpty() {
        final String base64Secret = "fd54a45s65fds737b9aafcb3412e07ed99b267f33413274720ddbb7f6c5e64e9f14075f2d7ed041592f0b7657baf8"; //ggignore
        ApplicationProperties applicationProperties = new ApplicationProperties();
        applicationProperties.setBase64JwtSecretKey(base64Secret);

        SecurityMetersService securityMetersService = new SecurityMetersService(new SimpleMeterRegistry());

        TokenProvider tokenProvider = new TokenProvider(applicationProperties, securityMetersService);

        Key key = (Key) ReflectionTestUtils.getField(tokenProvider, "key");
        assertThat(key).isNotNull().isEqualTo(Keys.hmacShaKeyFor(Decoders.BASE64.decode(base64Secret)));
    }

    private String createUnsupportedToken() {
        return Jwts.builder().setPayload("payload").signWith(key, TokenProvider.SIGNATURE_ALGORITHM).compact();
    }

    private String createTokenWithDifferentSignature() {
        Key otherKey = Keys.hmacShaKeyFor(
            Decoders.BASE64.decode("Xfd54a45s65fds737b9aafcb3412e07ed99b267f33413274720ddbb7f6c5e64e9f14075f2d7ed041592f0b7657baf8") //ggignore
        );

        return Jwts
            .builder()
            .setSubject("anonymous")
            .signWith(otherKey, TokenProvider.SIGNATURE_ALGORITHM)
            .setExpiration(new Date(new Date().getTime() + ONE_MINUTE))
            .compact();
    }
}
