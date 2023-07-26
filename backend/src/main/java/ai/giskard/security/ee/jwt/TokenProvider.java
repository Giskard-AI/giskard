package ai.giskard.security.ee.jwt;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.management.SecurityMetersService;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.GiskardUser;
import ai.giskard.web.dto.JWTToken;
import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.stereotype.Component;
import org.springframework.util.ObjectUtils;
import tech.jhipster.config.JHipsterProperties;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.security.SecureRandom;
import java.util.*;
import java.util.stream.Collectors;

@Component
public class TokenProvider {

    public static final int GENERATED_KEY_BITS = 256;
    public static final SignatureAlgorithm SIGNATURE_ALGORITHM = SignatureAlgorithm.HS256;
    private final Logger log = LoggerFactory.getLogger(TokenProvider.class);

    private static final String AUTHORITIES_KEY = "auth";
    private static final String ID = "id";
    private static final String TOKEN_TYPE_KEY = "token_type";

    private static final String INVALID_JWT_TOKEN = "Invalid JWT token.";

    private final Key key;

    private final JwtParser jwtParser;

    private final long tokenValidityInMilliseconds;
    private final long apiTokenValidityInMilliseconds;
    private final long invitationTokenValidityInMilliseconds;

    private final long tokenValidityInMillisecondsForRememberMe;

    private final SecurityMetersService securityMetersService;

    public TokenProvider(JHipsterProperties jHipsterProperties, ApplicationProperties applicationProperties, SecurityMetersService securityMetersService) {
        byte[] keyBytes;
        String base64SecretProperty = jHipsterProperties.getSecurity().getAuthentication().getJwt().getBase64Secret();
        String secretProperty = jHipsterProperties.getSecurity().getAuthentication().getJwt().getSecret();
        if (!ObjectUtils.isEmpty(base64SecretProperty)) {
            keyBytes = Decoders.BASE64.decode(base64SecretProperty);
            log.info("Using a provided Base64-encoded JWT secret key of {} bytes", keyBytes.length);
        } else if (secretProperty != null) {
            log.warn(
                "Warning: the JWT key used is not Base64-encoded. " +
                    "We recommend using the `jhipster.security.authentication.jwt.base64-secret` key for optimum security."
            );
            base64SecretProperty = secretProperty;
            keyBytes = base64SecretProperty.getBytes(StandardCharsets.UTF_8);
        } else {
            keyBytes = new byte[GENERATED_KEY_BITS / 8];
            new SecureRandom().nextBytes(keyBytes);
            String base64Key = Base64.getEncoder().encodeToString(keyBytes);
            log.info("No JWT secret key was specified in the configuration, generating a new one of {} bits: {}", GENERATED_KEY_BITS, base64Key);
        }
        key = Keys.hmacShaKeyFor(keyBytes);
        jwtParser = Jwts.parserBuilder().setSigningKey(key).build();
        this.tokenValidityInMilliseconds = 1000 * jHipsterProperties.getSecurity().getAuthentication().getJwt().getTokenValidityInSeconds();
        this.apiTokenValidityInMilliseconds = (long) 24 * 60 * 60 * 1000 * applicationProperties.getApiTokenValidityInDays();
        this.invitationTokenValidityInMilliseconds = (long) 24 * 60 * 60 * 1000 * applicationProperties.getInvitationTokenValidityInDays();
        this.tokenValidityInMillisecondsForRememberMe =
            1000 * jHipsterProperties.getSecurity().getAuthentication().getJwt().getTokenValidityInSecondsForRememberMe();

        this.securityMetersService = securityMetersService;
    }

    public JWTToken createToken(Authentication authentication, boolean rememberMe) {
        String authorities = authentication.getAuthorities().stream().map(GrantedAuthority::getAuthority).collect(Collectors.joining(","));

        long now = (new Date()).getTime();
        Date validity;
        if (rememberMe) {
            validity = new Date(now + this.tokenValidityInMillisecondsForRememberMe);
        } else {
            validity = new Date(now + this.tokenValidityInMilliseconds);
        }

        return createToken(authentication.getName(), ((GiskardUser) authentication.getPrincipal()).getId(), authorities, validity, key);
    }

    public static JWTToken createToken(String name, Long id, String authorities, Date validity, Key secretKey) {
        return new JWTToken(Jwts
            .builder()
            .setSubject(name)
            .claim(AUTHORITIES_KEY, authorities)
            .claim(ID, id)
            .claim(TOKEN_TYPE_KEY, JWTTokenType.UI)
            .signWith(secretKey, SIGNATURE_ALGORITHM)
            .setExpiration(validity)
            .compact(), validity.toInstant());
    }

    public JWTToken createAPIaccessToken(Authentication authentication) {
        String authorities = authentication.getAuthorities().stream().map(GrantedAuthority::getAuthority).collect(Collectors.joining(","));

        long now = (new Date()).getTime();
        Date expiration = new Date(now + this.apiTokenValidityInMilliseconds);
        return new JWTToken(Jwts
            .builder()
            .setSubject(authentication.getName())
            .claim(TOKEN_TYPE_KEY, JWTTokenType.API)
            .claim(AUTHORITIES_KEY, authorities)
            .signWith(key, SIGNATURE_ALGORITHM)
            .setExpiration(expiration)
            .compact(), expiration.toInstant());
    }

    public String createInvitationToken(String invitorEmail, String invitedEmail) {
        long now = (new Date()).getTime();
        return Jwts
            .builder()
            .setSubject(invitorEmail)
            .setAudience(invitedEmail)
            .claim(TOKEN_TYPE_KEY, JWTTokenType.INVITATION)
            .signWith(key, SIGNATURE_ALGORITHM)
            .setExpiration(new Date(now + this.invitationTokenValidityInMilliseconds))
            .compact();
    }


    public Authentication getAuthentication(String token) {
        Claims claims = jwtParser.parseClaimsJws(token).getBody();
        List<GrantedAuthority> authorities = new ArrayList<>();

        if (claims.get(AUTHORITIES_KEY) != null) {
            Arrays
                .stream(claims.get(AUTHORITIES_KEY).toString().split(","))
                .filter(auth -> !auth.trim().isEmpty())
                .map(SimpleGrantedAuthority::new).forEach(authorities::add);
        }
        if (JWTTokenType.API.name().equals(claims.get(TOKEN_TYPE_KEY))) {
            authorities.add(new SimpleGrantedAuthority(AuthoritiesConstants.API));
        }

        GiskardUser principal = new GiskardUser(claims.get(ID, Long.class), claims.getSubject(), "", authorities);

        return new UsernamePasswordAuthenticationToken(principal, token, authorities);
    }

    public boolean validateToken(String authToken) {
        return validateToken(authToken, null);
    }

    public boolean validateToken(String authToken, JWTTokenType tokenType) {
        try {
            Jws<Claims> claims = jwtParser.parseClaimsJws(authToken);
            if (tokenType != null) {
                JWTTokenType receivedTokenType = JWTTokenType.valueOf(claims.getBody().get(TOKEN_TYPE_KEY, String.class));
                if (tokenType != receivedTokenType) {
                    log.warn("Incorrect token type, expected {}, but received {}", tokenType, receivedTokenType);
                    return false;
                }
            }
            return true;
        } catch (ExpiredJwtException e) { // NOSONAR
            this.securityMetersService.trackTokenExpired();
            log.trace(INVALID_JWT_TOKEN, e);
            throw e;
        } catch (UnsupportedJwtException e) {
            this.securityMetersService.trackTokenUnsupported();

            log.trace(INVALID_JWT_TOKEN, e);
        } catch (MalformedJwtException e) {
            this.securityMetersService.trackTokenMalformed();

            log.trace(INVALID_JWT_TOKEN, e);
        } catch (SignatureException e) {
            this.securityMetersService.trackTokenInvalidSignature();

            log.trace(INVALID_JWT_TOKEN, e);
        } catch (IllegalArgumentException e) {
            log.error("Token validation error {}", e.getMessage());
        }

        return false;
    }
}
