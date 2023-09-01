package ai.giskard.web.rest;

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
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@AutoConfigureMockMvc
@IntegrationTest
class PublicApiControllerIT {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @Transactional
    @WithMockUser(username = "admin")
    void testApiAuthFail() throws Exception {
        mockMvc
            .perform(get("/public-api/ml-worker-connect").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isForbidden());
    }

    @Test
    @Transactional
    @WithMockUser(username = "admin", authorities = {AuthoritiesConstants.API})
    void testApiAuthPass() throws Exception {
        mockMvc
            .perform(get("/public-api/ml-worker-connect").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
    }
}
