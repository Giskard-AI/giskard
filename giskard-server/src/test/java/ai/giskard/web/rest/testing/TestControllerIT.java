package ai.giskard.web.rest.testing;

import ai.giskard.IntegrationTest;
import ai.giskard.security.AuthoritiesConstants;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "admin", authorities = AuthoritiesConstants.ADMIN)
class TestControllerIT {

    @Autowired
    private MockMvc restUserMockMvc;


    @Test
    @Transactional
    void getAllProjects() throws Exception {
        restUserMockMvc.perform(get("/api/v2/testing/tests/code-test-templates").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE))
            .andExpect(jsonPath("$.[*].title").isNotEmpty())
            .andExpect(jsonPath("$.[*].items").isNotEmpty());
    }
}
