package ai.giskard.web.rest;

import ai.giskard.IntegrationTest;
import ai.giskard.repository.ApiKeyRepository;
import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.result.MockMvcResultMatchers;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@AutoConfigureMockMvc
@IntegrationTest
class UserApiKeyControllerIT {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ApiKeyRepository apiKeyRepository;

    @Test
    @Transactional
    @WithMockUser(username = "admin")
    void testGetApiKeys() throws Exception {
        mockMvc
                .perform(get("/api/v2/apikey").contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(MockMvcResultMatchers.content().json("[]"));

        assertThat(apiKeyRepository.findAll()).isEmpty();

        int numberOfCreatedKeys = 2;
        for (int i = 0; i < numberOfCreatedKeys; i++) {
            mockMvc
                .perform(post("/api/v2/apikey").contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(i + 1)))
                .andExpect(jsonPath("$.[*].id").exists())
                .andExpect(jsonPath("$.[*].key").exists());
        }

        assertThat(apiKeyRepository.findAll()).hasSize(numberOfCreatedKeys);
    }

    @Test
    @Transactional
    @WithMockUser(username = "admin")
    void testDeleteApiKey() throws Exception {
        MvcResult response = mockMvc
            .perform(post("/api/v2/apikey").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(1)))
            .andExpect(jsonPath("$.[*].id").exists())
            .andExpect(jsonPath("$.[*].key").exists()).andReturn();

        String keyId = JsonPath.read(response.getResponse().getContentAsString(), "$.[0].id").toString();

        mockMvc
            .perform(delete("/api/v2/apikey/" + keyId).contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(0)));
        assertThat(apiKeyRepository.findAll()).isEmpty();

    }
}
