package ai.giskard.web.rest;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.User;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import org.apache.commons.lang3.RandomStringUtils;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@AutoConfigureMockMvc
@WithMockUser(authorities = AuthoritiesConstants.ADMIN)
@IntegrationTest
class AppConfigIT {
    private static final Logger log = LoggerFactory.getLogger(AppConfigIT.class);

    private static final String DEFAULT_LOGIN = "johndoe";

    private static final String DEFAULT_EMAIL = "johndoe@localhost";

    private static final String DEFAULT_DISPLAY_NAME = "john doe";

    @Autowired
    private BuildProperties buildProperties;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private MockMvc restUserMockMvc;

    /**
     * Create a User.
     * <p>
     * This is a static method, as tests for other entities might also need it,
     * if they test an entity which has a required relationship to the User entity.
     */
    public static User createUser() {
        User user = new User();
        user.setLogin(DEFAULT_LOGIN + RandomStringUtils.randomAlphabetic(5));
        user.setPassword(RandomStringUtils.random(60));
        user.setActivated(true);
        user.setEmail(RandomStringUtils.randomAlphabetic(5) + DEFAULT_EMAIL);
        return user;
    }

    /**
     * Setups the database with one user.
     */
    public static void initTestUser(UserRepository userRepository) {
        User user = createUser();
        user.setLogin(DEFAULT_LOGIN);
        user.setDisplayName(DEFAULT_DISPLAY_NAME);
        user.setEmail(DEFAULT_EMAIL);
        User createdUser = userRepository.saveAndFlush(user);
        log.info("Created User {}", createdUser);
    }
    @Autowired
    DataSource dataSource;

    @Test
    @Transactional
    @WithMockUser(value = DEFAULT_LOGIN)
    void getMe() throws Exception {
        initTestUser(userRepository);

        ResultActions perform = restUserMockMvc
            .perform(get("/api/v2/settings").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE))
            .andExpect(jsonPath("$.[*].giskardVersion").value(buildProperties.getVersion()))
            .andExpect(jsonPath("$.[*].user_id").value(DEFAULT_LOGIN))
            .andExpect(jsonPath("$.[*].displayName").value(DEFAULT_DISPLAY_NAME));
    }
}
