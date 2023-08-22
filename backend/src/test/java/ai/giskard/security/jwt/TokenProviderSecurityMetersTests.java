package ai.giskard.security.jwt;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.management.SecurityMetersService;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.ee.jwt.TokenProvider;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;

import java.security.Key;
import java.util.Collection;
import java.util.Date;

import static ai.giskard.security.jwt.JWTFilterTest.createAuthentication;
import static org.assertj.core.api.Assertions.assertThat;

class TokenProviderSecurityMetersTests {

    private static final long ONE_MINUTE = 60000;
    private static final String INVALID_TOKENS_METER_EXPECTED_NAME = "security.authentication.invalid-tokens";

    private MeterRegistry meterRegistry;

    private TokenProvider tokenProvider;

    @BeforeEach
    public void setup() {
        ApplicationProperties applicationProperties = new ApplicationProperties();
        String base64Secret = "fd54a45s65fds737b9aafcb3412e07ed99b267f33413274720ddbb7f6c5e64e9f14075f2d7ed041592f0b7657baf8";
        applicationProperties.setBase64JwtSecretKey(base64Secret);

        meterRegistry = new SimpleMeterRegistry();

        SecurityMetersService securityMetersService = new SecurityMetersService(meterRegistry);

        tokenProvider = new TokenProvider(applicationProperties, securityMetersService);
        Key key = Keys.hmacShaKeyFor(Decoders.BASE64.decode(base64Secret));

        ReflectionTestUtils.setField(tokenProvider, "key", key);
        ReflectionTestUtils.setField(tokenProvider, "tokenValidityInMilliseconds", ONE_MINUTE);
    }

    @Test
    void testValidTokenShouldNotCountAnything() {
        Collection<Counter> counters = meterRegistry.find(INVALID_TOKENS_METER_EXPECTED_NAME).counters();

        assertThat(aggregate(counters)).isZero();

        String validToken = createValidToken();

        tokenProvider.validateToken(validToken);

        assertThat(aggregate(counters)).isZero();
    }

    @Test
    void testTokenExpiredCount() {
        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "expired").counter().count()).isZero();

        String expiredToken = createExpiredToken();

        Assertions.assertThrows(ExpiredJwtException.class, () -> tokenProvider.validateToken(expiredToken));

        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "expired").counter().count()).isEqualTo(1);
    }

    @Test
    void testTokenUnsupportedCount() {
        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "unsupported").counter().count()).isZero();

        String unsupportedToken = createUnsupportedToken();

        tokenProvider.validateToken(unsupportedToken);

        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "unsupported").counter().count()).isEqualTo(1);
    }

    @Test
    void testTokenSignatureInvalidCount() {
        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "invalid-signature").counter().count()).isZero();

        String tokenWithDifferentSignature = createTokenWithDifferentSignature();

        tokenProvider.validateToken(tokenWithDifferentSignature);

        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "invalid-signature").counter().count()).isEqualTo(1);
    }

    @Test
    void testTokenMalformedCount() {
        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "malformed").counter().count()).isZero();

        String malformedToken = createMalformedToken();

        tokenProvider.validateToken(malformedToken);

        assertThat(meterRegistry.get(INVALID_TOKENS_METER_EXPECTED_NAME).tag("cause", "malformed").counter().count()).isEqualTo(1);
    }

    private String createValidToken() {
        Authentication authentication = createAuthentication(AuthoritiesConstants.AITESTER);

        return tokenProvider.createToken(authentication, false).getToken();
    }

    private String createExpiredToken() {
        ReflectionTestUtils.setField(tokenProvider, "tokenValidityInMilliseconds", -ONE_MINUTE);

        Authentication authentication = createAuthentication(AuthoritiesConstants.AITESTER);

        return tokenProvider.createToken(authentication, false).getToken();
    }

    private String createUnsupportedToken() {
        Key key = (Key) ReflectionTestUtils.getField(tokenProvider, "key");

        return Jwts.builder().setPayload("payload").signWith(key, TokenProvider.SIGNATURE_ALGORITHM).compact();
    }

    private String createMalformedToken() {
        String validToken = createValidToken();

        return "X" + validToken;
    }

    private String createTokenWithDifferentSignature() {
        Key otherKey = Keys.hmacShaKeyFor(
            Decoders.BASE64.decode("Xfd54a45s65fds737b9aafcb3412e07ed99b267f33413274720ddbb7f6c5e64e9f14075f2d7ed041592f0b7657baf8")
        );

        return Jwts
            .builder()
            .setSubject("anonymous")
            .signWith(otherKey, TokenProvider.SIGNATURE_ALGORITHM)
            .setExpiration(new Date(new Date().getTime() + ONE_MINUTE))
            .compact();
    }

    private double aggregate(Collection<Counter> counters) {
        return counters.stream().mapToDouble(Counter::count).sum();
    }
}
