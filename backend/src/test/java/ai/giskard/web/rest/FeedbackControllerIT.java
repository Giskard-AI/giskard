package ai.giskard.web.rest;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Feedback;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.mock.FeedbackMock;
import ai.giskard.mock.MockUser;
import ai.giskard.mock.ProjectMock;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import org.assertj.core.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for the {@link ai.giskard.web.rest.controllers.FeedbackController} REST controller.
 */
@AutoConfigureMockMvc
@WithMockGiskardUser
@IntegrationTest
class FeedbackControllerIT {

    @Autowired
    private FeedbackRepository feedbackRepository;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private ProjectRepository projectRepository;
    @Autowired
    private MockMvc restFeedbackMockMvc;
    @Test
    @WithUnauthenticatedMockUser
    void testDeleteWithUnauthenticatedUser() throws Exception {
        restFeedbackMockMvc
            .perform(delete("/api/v2/feedbacks/{feedbackId}", 1L)
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isForbidden());
    }

    @Test
    @Transactional
    void testDeleteAdminAllowedToDelete() throws Exception {
        User creator = userRepository.save(MockUser.mockUser(AuthoritiesConstants.AITESTER));
        Project project = projectRepository.save(ProjectMock.mockProject(creator));
        Feedback feedback = feedbackRepository.save(FeedbackMock.mockFeedback(project, creator));

        restFeedbackMockMvc
            .perform(delete("/api/v2/feedbacks/{feedbackId}", feedback.getId())
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isNoContent());

        Assertions.assertThat(feedbackRepository.findOneById(feedback.getId()))
            .isNull();
    }

    @Test
    @WithMockGiskardUser(userId = Long.MAX_VALUE, roles = {})
    @Transactional
    void testDeleteUnauthorizedUser() throws Exception {
        User creator = userRepository.save(MockUser.mockUser(AuthoritiesConstants.AITESTER));
        Project project = projectRepository.save(ProjectMock.mockProject(creator));
        Feedback feedback = feedbackRepository.save(FeedbackMock.mockFeedback(project, creator));

        restFeedbackMockMvc
            .perform(delete("/api/v2/feedbacks/{feedbackId}", feedback.getId())
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isUnauthorized())
            .andExpect(jsonPath("$.title").value("Unauthorized"))
            .andExpect(jsonPath("$.detail").value("Unauthorized to Delete Feedback"));


        Assertions.assertThat(feedbackRepository.findOneById(feedback.getId()))
            .isEqualTo(feedback);
    }

}
