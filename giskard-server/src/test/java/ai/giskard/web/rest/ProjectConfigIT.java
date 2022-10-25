package ai.giskard.web.rest;

import ai.giskard.IntegrationTest;
import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.InspectionSettings;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import org.apache.commons.lang3.RandomStringUtils;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;

@AutoConfigureMockMvc
@WithMockUser(authorities = AuthoritiesConstants.ADMIN)
@IntegrationTest
class ProjectConfigIT {

    private static final String DEFAULT_PROJECT_NAME = "Test Project";
    private static final String DEFAULT_PROJECT_KEY = "test_project";
    private static final String DEFAULT_USER_LOGIN = "john";
    private static final String DEFAULT_EMAIL = "john@gmail.com";
    private static final String DEFAULT_DISPLAY_NAME = "John";


    @Autowired
    ApplicationProperties applicationProperties;

    @Autowired
    ProjectRepository projectRepository;

    @Autowired
    UserRepository userRepository;

    @Autowired
    MockMvc mockMvc;

    public Project initProject(){
        User user = new User();
        user.setLogin(DEFAULT_USER_LOGIN);
        user.setDisplayName(DEFAULT_DISPLAY_NAME);
        user.setEmail(DEFAULT_EMAIL);
        user.setPassword(RandomStringUtils.random(60));
        userRepository.saveAndFlush(user);

        Project project = new Project();
        project.setName(DEFAULT_PROJECT_NAME);
        project.setKey(DEFAULT_PROJECT_KEY);
        project.setDescription("");
        project.setOwner(user);
        return project;
    }

    @Test
    @Transactional
    void getNumberSamplesDefaultProject() throws Exception {
        Project project = initProject();
        projectRepository.saveAndFlush(project);
        mockMvc.perform(get(String.format("/api/v2/project?key=%s", DEFAULT_PROJECT_KEY)).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.inspectionSettings.limeNumberSamples").value(applicationProperties.getLimeNumberSamples()))
            .andExpect(jsonPath("$.key").value(DEFAULT_PROJECT_KEY));
    }

    @Test
    @Transactional
    void modifiedNumberSamples() throws Exception {
        Project project = initProject();
        InspectionSettings inspectionSettings = new InspectionSettings();
        inspectionSettings.setLimeNumberSamples(1000);
        project.setInspectionSettings(inspectionSettings);
        projectRepository.saveAndFlush(project);
        mockMvc.perform(get(String.format("/api/v2/project?key=%s", DEFAULT_PROJECT_KEY)).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.inspectionSettings.limeNumberSamples").value(1000))
            .andExpect(jsonPath("$.key").value(DEFAULT_PROJECT_KEY));
    }
}
