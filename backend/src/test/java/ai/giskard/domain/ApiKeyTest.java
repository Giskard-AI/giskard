package ai.giskard.domain;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApiKeyTest {

    @Test
    void testApiKeyConstructor() {
        ApiKey apiKey = new ApiKey(new User());
        assertNotNull(apiKey.getId());
        String key = apiKey.getKey();
        assertNotNull(key);
        String pattern = ApiKey.PREFIX + "[a-zA-Z0-9]{" + (ApiKey.KEY_LENGTH - ApiKey.PREFIX.length()) + "}";
        assertTrue(key.matches(pattern), "Key should match pattern: " + pattern);
    }
}
