package ai.giskard.mock;

import ai.giskard.domain.User;

public class MockUser {

    private final static String HASHED_PASSWORD = "A".repeat(60);

    public static User mockUser(String username) {
        final User user = new User();

        user.setLogin(username);
        user.setEmail(String.format("%s@giskard.ai", username));
        user.setPassword(HASHED_PASSWORD);

        return user;
    }
}
