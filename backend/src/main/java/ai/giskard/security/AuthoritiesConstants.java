package ai.giskard.security;

import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Constants for Spring Security authorities.
 */
@Component("AuthoritiesConstants")
public final class AuthoritiesConstants {

    public static final String ADMIN = "ROLE_ADMIN";
    public static final String API = "API";

    public static final String AICREATOR = "ROLE_AICREATOR";

    public static final String AITESTER = "ROLE_AITESTER";

    public static final String HF_SUPERUSER = "ROLE_HFSU";

    public static final Map<String, String> AUTHORITY_NAMES = Map.of(
        AICREATOR, "AI Creator",
        AITESTER, "AI Tester",
        ADMIN, "Admin",
        HF_SUPERUSER, "HF Superuser"
    );

    private AuthoritiesConstants() {
    }
}
