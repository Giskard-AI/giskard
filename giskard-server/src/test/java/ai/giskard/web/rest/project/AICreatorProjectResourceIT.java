package ai.giskard.web.rest.project;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.service.mapper.GiskardMapper;
import ai.giskard.web.rest.InitService;
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
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for the {@link ProjectController} REST controller with AICreator authorities
 */
@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "aicreator", authorities = AuthoritiesConstants.AICREATOR)
class AICreatorProjectResourceIT extends ProjectResourceIT {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private InitService userTestService;

    @Autowired
    private MockMvc restUserMockMvc;

    @Autowired
    private GiskardMapper giskardMapper;

    User loggedUser;

    public static String PROJECTKEY = "AICREATORProject";
    public static String USERKEY = "aicreator";


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
            .andExpect(content().string(CoreMatchers.not(containsString("ADMINProject"))));
    }


    /**
     * Create new Project
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void create() throws Exception {
        ProjectPostDTO projectDTO = new ProjectPostDTO();
        projectDTO.setName("createdProject");
        projectDTO.setKey("keyProject");
        restUserMockMvc.perform(post("/api/v2/project").contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectDTO)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("createdProject"))
            .andExpect(jsonPath("$.key").value("keyProject"));
        assertThat(projectRepository.findOneByName("createdProject")).isPresent();
    }


    /**
     * Update Project
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void update() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        User user = userRepository.getOneByLogin(USERKEY);
        ProjectPostDTO projectPostDTO = giskardMapper.projectToProjectPostDTO(project);
        projectPostDTO.setName("updateProject");
        projectPostDTO.setKey("updateKey");

        project.setOwner(user);
        project.setName("updateProject");
        project.setKey("updateKey");
        restUserMockMvc.perform(put("/api/v2/project/" + project.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(project)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("updateProject"))
            .andExpect(jsonPath("$.key").value("updateKey"));
        assertThat(projectRepository.findOneByName("updateProject")).isPresent();
    }


    /**
     * Remove project
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void remove() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        restUserMockMvc.perform(delete("/api/v2/project/" + project.getId()).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Optional<Project> projectOptional = projectRepository.findOneByName(PROJECTKEY);
        assertThat(projectOptional).isEmpty();
    }

    /**
     * Add user to project's guestlist
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void addGuest() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        User user = userRepository.getOneByLogin(USERKEY);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        assertThat(project.getGuests()).isNullOrEmpty();
        restUserMockMvc.perform(put(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Project updatedProject = projectRepository.getOneByName(PROJECTKEY);
        assertThat(updatedProject.getGuests()).contains(user);
    }

    /**
     * Remove user from the guestlist
     *
     * @throws Exception
     */
    @Override
    @Test
    @Transactional
    void removeGuest() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        User user = userRepository.getOneByLogin(USERKEY);
        project.addGuest(user);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        restUserMockMvc.perform(delete(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Project updatedProject = projectRepository.getOneWithGuestsById(project.getId());
        assertThat(updatedProject.getGuests()).doesNotContain(user);
    }

}
