package ai.giskard.web.rest.errors;

import ai.giskard.IntegrationTest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests {@link GlobalExceptionHandler} controller advice.
 */
@WithMockUser
@AutoConfigureMockMvc
@IntegrationTest
class ExceptionTranslatorIT {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void testConcurrencyFailure() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/concurrency-failure"))
            .andExpect(status().isConflict())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.title").value("Conflict"));
    }

    @Test
    void testMethodArgumentNotValid() throws Exception {
        mockMvc
            .perform(post("/api/exception-translator-test/method-argument").content("{}").contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.detail").value("Invalid request content."));
    }

    @Test
    void testMissingServletRequestPartException() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/missing-servlet-request-part"))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.detail").value("Required part 'part' is not present."));
    }

    @Test
    void testMissingServletRequestParameterException() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/missing-servlet-request-parameter"))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.detail").value("Required parameter 'param' is not present."));
    }

    @Test
    void testAccessDenied() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/access-denied"))
            .andExpect(status().isForbidden())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.detail").value("test access denied!"));
    }

    @Test
    void testUnauthorized() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/unauthorized"))
            .andExpect(status().isUnauthorized())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.title").value("Unauthorized"))
            .andExpect(jsonPath("$.instance").value("/api/exception-translator-test/unauthorized"))
            .andExpect(jsonPath("$.detail").value("test authentication failed!"));
    }

    @Test
    void testMethodNotSupported() throws Exception {
        mockMvc
            .perform(post("/api/exception-translator-test/access-denied"))
            .andExpect(status().isMethodNotAllowed())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.detail").value("Method 'POST' is not supported."));
    }

    @Test
    void testInternalServerError() throws Exception {
        mockMvc
            .perform(get("/api/exception-translator-test/internal-server-error"))
            .andExpect(status().isInternalServerError())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.title").value("Internal Server Error"));
    }
}
