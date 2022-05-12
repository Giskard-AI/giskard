package ai.giskard.web.rest.project;

import ai.giskard.IntegrationTest;
import ai.giskard.config.InitService;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.web.temp.TestGiskardMapper;
import ai.giskard.web.temp.TestProjectPostDTO;
import ai.giskard.web.rest.controllers.ProjectController;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for the {@link ProjectController} REST controller.
 */
@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "admin", authorities = AuthoritiesConstants.ADMIN)
class ProjectMapperIT {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private InitService initService;

    @Autowired
    private MockMvc restUserMockMvc;
    @Autowired
    private TestGiskardMapper testGiskardMapper;

    User loggedUser;

    public String PROJECTKEY;
    public String USERKEY;

    protected void initKeys() {
        this.USERKEY = initService.getUserName("admin");
        this.PROJECTKEY = initService.getProjectName("admin");
    }

    @BeforeEach
    public void initTest() {
        initService.init();
        initKeys();
        loggedUser = userRepository.getOneByLogin(USERKEY);
    }

//
//    /**
//     * Create new Project
//     *
//     * @throws Exception
//     */
//    @Test
//    @Transactional
//    void create() throws Exception {
//        ProjectPostDTO projectDTO = new ProjectPostDTO();
//        projectDTO.setName("createdProject");
//        projectDTO.setKey("keyProject");
//        restUserMockMvc.perform(post("/api/v2/project").contentType(MediaType.APPLICATION_JSON)
//                .content(new ObjectMapper().writeValueAsString(projectDTO)))
//            .andExpect(status().isOk())
//            .andExpect(jsonPath("$.name").value("createdProject"))
//            .andExpect(jsonPath("$.key").value("keyProject"));
//        assertThat(projectRepository.findOneByName("createdProject")).isPresent();
//    }
//

    /**
     * Update Project
     *
     * @throws Exception
     */
    @Test
    void update() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        assertThat(project.getOwner().getLogin()).isEqualTo("admin");
        User aiTester=userRepository.findOneByLogin(initService.getUserName("aitester")).orElseThrow(()->new EntityNotFoundException(Entity.USER, "ai tester"));
        TestProjectPostDTO projectPostDTO = testGiskardMapper.projectToProjectPostDTO(project);
        projectPostDTO.setName("updateProject");
        projectPostDTO.setKey("updateKey");
        projectPostDTO.setOwner(aiTester);
        restUserMockMvc.perform(put("/api/v2/_project/" + project.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectPostDTO))).andExpect(status().is5xxServerError());

    }

    /**
     * Update Project
     *
     * @throws Exception
     */
    @Test
    void updateTransactional() throws Exception {
        Project project = projectRepository.getOneByName(PROJECTKEY);
        assertThat(project.getOwner().getLogin()).isEqualTo("admin");
        User aiTester=userRepository.findOneByLogin(initService.getUserName("aitester")).orElseThrow(()->new EntityNotFoundException(Entity.USER, "ai tester"));
        TestProjectPostDTO projectPostDTO = testGiskardMapper.projectToProjectPostDTO(project);
        projectPostDTO.setName("updateProject");
        projectPostDTO.setKey("updateKey");
        projectPostDTO.setOwner(aiTester);
        restUserMockMvc.perform(put("/api/v2/_project_t/" + project.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(projectPostDTO)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("updateProject"))
            .andExpect(jsonPath("$.key").value("updateKey"))
            .andExpect(jsonPath("$.owner_details.user_id").value("aitester"));

        assertThat(projectRepository.findOneByName("updateProject")).isPresent();
    }

}
