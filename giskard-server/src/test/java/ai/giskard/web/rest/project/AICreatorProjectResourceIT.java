package ai.giskard.web.rest.project;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.init.InitService;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.controllers.ProjectController;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.hamcrest.CoreMatchers;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.CoreMatchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Integration tests for the {@link ProjectController} REST controller with AICreator authorities
 */
@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "aicreator", authorities = AuthoritiesConstants.AICREATOR)
class AICreatorProjectResourceIT extends AdminProjectResourceIT {

    @Autowired
    private ProjectRepository projectRepository;


    @Autowired
    private MockMvc restUserMockMvc;

    @Autowired
    private GiskardMapper giskardMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private InitService initService;

    @Override
    protected void initKeys() {
        this.USERKEY = initService.getUserName("aicreator");
        this.PROJECTKEY = initService.getProjectName("aicreator");
        this.OTHERUSERKEY = initService.getUserName("admin");
        this.OTHERPROJECTKEY = initService.getProjectName("admin");
    }

    /**
     * Get all Projects
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void getAllProjects() throws Exception {
        restUserMockMvc.perform(get("/api/v2/project").accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE))
            .andExpect(content().string(containsString(PROJECTKEY)))
            .andExpect(content().string(CoreMatchers.not(containsString(OTHERPROJECTKEY))));
    }

    /**
     * Update project when not owner
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void updateNotOwner() throws Exception {
        Project project = projectRepository.getOneByName(OTHERPROJECTKEY);
        ProjectPostDTO projectPostDTO = giskardMapper.projectToProjectPostDTO(project);
        projectPostDTO.setName("updateProject");
        projectPostDTO.setKey("updateKey");
        restUserMockMvc.perform(put("/api/v2/project/" + project.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectPostDTO)))
            .andExpect(status().is4xxClientError());
        assertThat(projectRepository.findOneByName("updateProject")).isEmpty();
    }


    /**
     * Remove project when not owner
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void removeNotOwner() throws Exception {
        Project project = projectRepository.getOneByName(OTHERPROJECTKEY);
        restUserMockMvc.perform(delete("/api/v2/project/" + project.getId()).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().is4xxClientError());
        Optional<Project> projectOptional = projectRepository.findOneByName(OTHERPROJECTKEY);
        assertThat(projectOptional).isPresent();
    }

    /**
     * Add user to project's guestlist when not owner
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void addGuestNotOwner() throws Exception {
        Project project = projectRepository.getOneByName(OTHERPROJECTKEY);
        User user = userRepository.getOneByLogin(USERKEY);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        assertThat(project.getGuests()).isNullOrEmpty();
        restUserMockMvc.perform(put(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().is4xxClientError());
        Project updatedProject = projectRepository.getOneByName(PROJECTKEY);
        assertThat(updatedProject.getGuests()).doesNotContain(user);
    }
}
