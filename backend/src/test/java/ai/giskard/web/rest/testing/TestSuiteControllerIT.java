package ai.giskard.web.rest.testing;

import ai.giskard.IntegrationTest;
import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.InitService;
import ai.giskard.web.dto.TestSuiteDTO;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import org.springframework.http.MediaType;

import java.util.ArrayList;


@AutoConfigureMockMvc
@IntegrationTest
@WithMockUser(username = "admin", authorities = AuthoritiesConstants.ADMIN)
class TestSuiteControllerIT {

    @Autowired
    private MockMvc restUserMockMvc;

    @Autowired
    ProjectRepository projectRepository;


    @Autowired
    private InitService initService;

    @Test
    @Transactional
    void saveTestSuite() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin("admin"));

        TestSuiteDTO testSuiteDTO = new TestSuiteDTO();
        testSuiteDTO.setName("My test suite");
        testSuiteDTO.setProjectKey(project.getKey());
        testSuiteDTO.setTests(new ArrayList<>());

        restUserMockMvc.perform(post("/api/v2/testing/project/" + project.getKey() + "/suites")
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(testSuiteDTO)))
                .andExpect(status().isOk());

    }

    @Test
    @Transactional
    void saveTestSuiteWithEmptyName() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin("admin"));

        TestSuiteDTO testSuiteDTO = new TestSuiteDTO();
        testSuiteDTO.setProjectKey(project.getKey());
        testSuiteDTO.setTests(new ArrayList<>());

        restUserMockMvc.perform(post("/api/v2/testing/project/" + project.getKey() + "/suites")
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(testSuiteDTO)))
                .andExpect(status().is5xxServerError());

    }
}
