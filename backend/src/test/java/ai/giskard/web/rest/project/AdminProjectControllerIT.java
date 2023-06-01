package ai.giskard.web.rest.project;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.FileLocationService;
import ai.giskard.service.InitService;
import ai.giskard.web.dto.PostImportProjectDTO;
import ai.giskard.web.dto.PrepareImportProjectDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.rest.controllers.ProjectController;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.CoreMatchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for the {@link ProjectController} REST controller.
 */
@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "admin", authorities = AuthoritiesConstants.ADMIN)
class AdminProjectControllerIT {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private FileLocationService fileLocationService;

    @Autowired
    private InitService initService;

    @Autowired
    private MockMvc restUserMockMvc;

    @Autowired
    private GiskardMapper giskardMapper;

    User loggedUser;

    public String PROJECTKEY;
    public String USERKEY;
    public String OTHERUSERKEY;
    public String OTHERPROJECTKEY;

    protected void initKeys() {
        this.USERKEY = initService.getUserName("admin");
        this.PROJECTKEY = initService.getProjectByCreatorLogin("admin");
        this.OTHERUSERKEY = initService.getUserName("aicreator");
        this.OTHERPROJECTKEY = initService.getProjectByCreatorLogin("aicreator");
    }

    @BeforeEach
    public void initTest() {
        initService.init();
        initKeys();
        loggedUser = userRepository.getOneByLogin(USERKEY);
    }


    /**
     * Get all Projects
     */
    @Test
    @Transactional
    void getAllProjects() throws Exception {
        restUserMockMvc.perform(get("/api/v2/projects").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE))
            .andExpect(content().string(containsString(PROJECTKEY)))
            .andExpect(jsonPath("$", hasSize(projectRepository.findAll().size())));
    }

    /**
     * Get all projects with user not in database authority
     * Expect NotInDatabaseException
     */
    @Test
    @Transactional
    @WithMockUser(username = "notInDatabaseUser", authorities = AuthoritiesConstants.ADMIN)
    void getAllProjectsWithUnknownUser() throws Exception {
        restUserMockMvc.perform(get("/api/v2/projects").accept(MediaType.APPLICATION_JSON)).andExpect(status().isBadRequest());
    }

    /**
     * Show a project
     */
    @Test
    @Transactional
    void show() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        restUserMockMvc.perform(get(String.format("/api/v2/project?id=%d", project.getId())).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON_VALUE))
            .andExpect(content().string(containsString(PROJECTKEY)));
    }

    /**
     * Create new Project
     */
    @Test
    @Transactional
    void create() throws Exception {
        ProjectPostDTO projectDTO = new ProjectPostDTO();
        projectDTO.setName("createdProject");
        projectDTO.setKey("key_project");
        restUserMockMvc.perform(post("/api/v2/project").contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectDTO)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("createdProject"))
            .andExpect(jsonPath("$.key").value("key_project")); // Slug version
        assertThat(projectRepository.findOneByName("createdProject")).isPresent();
    }


    /**
     * Update Project
     */
    @Test
    @Transactional
    void update() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        ProjectPostDTO projectPostDTO = giskardMapper.projectToProjectPostDTO(project);
        projectPostDTO.setName("updateProject");
        projectPostDTO.setKey("updateKey");
        restUserMockMvc.perform(put("/api/v2/project/" + project.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectPostDTO)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("updateProject"))
            .andExpect(jsonPath("$.key").value("updateKey"));
        assertThat(projectRepository.findOneByName("updateProject")).isPresent();
    }

    /**
     * Update project when not owner
     */
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
            .andExpect(status().isOk());
        assertThat(projectRepository.findOneByName("updateProject")).isPresent();
    }


    /**
     * Remove project
     */
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
     */
    @Test
    @Transactional
    void addGuest() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        User user = userRepository.getOneByLogin(USERKEY);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        assertThat(project.getGuests()).isNullOrEmpty();
        restUserMockMvc.perform(put(url).accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());
        Project updatedProject = projectRepository.getOneByName(PROJECTKEY);
        assertThat(updatedProject.getGuests()).contains(user);
    }

    @Test
    @Transactional
    @Disabled("restore after the rest of demo projects are recreated")
    void exportImportProject() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        String url = String.format("/api/v2/download/project/%d/export", project.getId());
        assertThat(project.getKey()).isEqualTo(project.getKey());
        ResultActions resultActions = restUserMockMvc.perform(get(url))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_OCTET_STREAM));
        byte[] res = resultActions.andReturn().getResponse().getContentAsByteArray();
        String unzipUrl = "/api/v2/project/import/prepare";
        resultActions = restUserMockMvc.perform(multipart(unzipUrl).file(new MockMultipartFile("file", res)))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.projectKeyAlreadyExists").value(true));
        ObjectMapper objectMapper = new ObjectMapper();
        PrepareImportProjectDTO prepareImportProjectDTO = objectMapper.readValue(resultActions.andReturn().getResponse().getContentAsString(), PrepareImportProjectDTO.class);
        String nonConflictKey = "imported_credit";
        PostImportProjectDTO projectDTO = new PostImportProjectDTO(new HashMap<>(), nonConflictKey, prepareImportProjectDTO.getTemporaryMetadataDirectory());
        String urlImport = "/api/v2/project/import";
        restUserMockMvc.perform(post(urlImport).content(new ObjectMapper().writeValueAsString(projectDTO)).contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON))
            .andExpect(jsonPath("$.key").value(nonConflictKey))
            .andExpect(jsonPath("$.owner.user_id").value(userRepository.getOneByLogin(USERKEY).getLogin()));
    }


    /**
     * Remove user from the guestlist
     */
    @Test
    @Transactional
    void removeGuest() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        User user = userRepository.getOneByLogin(OTHERUSERKEY);
        project.addGuest(user);
        String url = String.format("/api/v2/project/%d/guests/%d", project.getId(), user.getId());
        restUserMockMvc.perform(delete(url).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk());
        Project updatedProject = projectRepository.findOneWithGuestsById(project.getId()).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, project.getId()));
        assertThat(updatedProject.getGuests()).isEmpty();
    }

}
