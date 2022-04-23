package ai.giskard.security;

/**
 * Constants for Spring Security authorities.
 */
public final class AuthoritiesConstants {

    public static final String ADMIN = "ROLE_ADMIN";

    public static final String AICREATOR = "ROLE_AICREATOR";

    public static final String AITESTER = "ROLE_AITESTER";

    public static final String[] authorities = new String[]{ADMIN, AITESTER, AICREATOR};

    private AuthoritiesConstants() {
    }
}
