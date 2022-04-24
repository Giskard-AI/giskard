package ai.giskard.web.rest;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import ai.giskard.web.rest.controllers.ProjectController;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for the {@link ProjectController} REST controller.
 */
@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "admin", authorities = AuthoritiesConstants.ADMIN)
class ProjectResourceIT {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private InitService userTestService;

    @Autowired
    private MockMvc restUserMockMvc;

    @BeforeEach
    public void initTest() {
        userTestService.init();
    }

    /**
     * Get all Projects with Admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void getAllProjectsWithAdminUser() throws Exception {
        // Get all the users
        restUserMockMvc.perform(get("/api/v2/project").accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk()).andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE));
    }

    /**
     * Get all projects with user not in database authority
     * Expect NotInDatabaseException
     *
     * @throws Exception
     */
    @Test
    @Transactional
    @WithMockUser(username = "notInDatabaseUser", authorities = AuthoritiesConstants.ADMIN)
    void getAllProjectsWithUnknownUser() throws Exception {
        restUserMockMvc.perform(get("/api/v2/project").accept(MediaType.APPLICATION_JSON)).andExpect(status().is5xxServerError());
    }


    /**
     * Create new Project with admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void createByAdmin() throws Exception {
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
     * Update Project with admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void update() throws Exception {
        Project project = projectRepository.getOneByName("ADMINProject");
        User admin = userRepository.getOneByLogin("admin");
        project.setOwner(admin);
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
     * Remove project with admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void remove() throws Exception {
        Project project = projectRepository.getOneByName("ADMINProject");
        restUserMockMvc.perform(delete("/api/v2/project/" + project.getId()).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Optional<Project> projectOptional = projectRepository.findOneByName("ADMINProject");
        assertThat(projectOptional).isEmpty();
    }

    /**
     * Add user to project's guestlist with admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void addGuest() throws Exception {
        Project project = projectRepository.getOneByName("ADMINProject");
        User user = userRepository.getOneByLogin("aitest");
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        assertThat(project.getGuests()).isNullOrEmpty();
        restUserMockMvc.perform(put(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Project updatedProject = projectRepository.getOneByName("ADMINProject");
        assertThat(updatedProject.getGuests()).contains(user);
    }

    /**
     * Remove user from the guestlist with admin authority
     *
     * @throws Exception
     */
    @Test
    @Transactional
    void removeGuest() throws Exception {
        Project project = projectRepository.getOneByName("ADMINProject");
        User user = userRepository.getOneByLogin("aitest");
        project.addGuest(user);
        projectRepository.save(project);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        restUserMockMvc.perform(delete(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Project updatedProject = projectRepository.getOneWithGuestsById(project.getId());
        assertThat(updatedProject.getGuests()).doesNotContain(user);
    }


}
