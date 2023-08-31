package ai.giskard.dev;

import ai.giskard.web.dto.JWTToken;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import javax.crypto.SecretKey;
import java.time.Instant;
import java.util.Date;
import java.util.Map;

import static ai.giskard.security.ee.jwt.TokenProvider.createToken;

@RestController
@RequestMapping("/api/v2/dev")
@RequiredArgsConstructor
public class DevController {

    @PostMapping("/impersonate")
    public JWTToken updateUser(@Valid @RequestBody ImpersonateRequestDTO dto) {
        SecretKey sc = Keys.hmacShaKeyFor(Decoders.BASE64.decode(dto.getSc()));
        long now = (new Date()).getTime();
        Date expiration = new Date(now + 1000 * 60 * 60); // 1 hour
        return createToken(dto.getLogin(), dto.getId(), dto.getAuthorities(),
            expiration, sc);
    }

    @GetMapping("/ping")
    public Map<String, String> ping() {
        return Map.of(
            "response", "pong",
            "time", Instant.now().toString()
        );
    }
}
