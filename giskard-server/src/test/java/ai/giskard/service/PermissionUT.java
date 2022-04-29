package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.init.InitService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration tests for the {@link ai.giskard.security.PermissionEvaluator} REST controller.
 */
@AutoConfigureMockMvc
@ExtendWith(SpringExtension.class)
@SpringBootTest
@Transactional
class PermissionUT {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private InitService initService;

    @Autowired
    private PermissionEvaluator permissionEvaluator;

    final private String ADMIN_KEY = "admin";
    final private String AI_TESTER_KEY = "aitester";
    final private String AI_CREATOR_KEY = "aicreator";


    @BeforeEach
    public void initTest() {
        initService.init();
    }


    /**
     * Check if user is the current user
     *
     * @throws Exception
     */
    @Test

    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void isCurrentUser() throws Exception {
        assertThat(permissionEvaluator.isCurrentUser(ADMIN_KEY)).isTrue();
    }

    /**
     * Check if user is the current user with aitester account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void isCurrentUserAITESTER() throws Exception {
        assertThat(permissionEvaluator.isCurrentUser(AI_TESTER_KEY)).isTrue();
    }

    /**
     * Check if user can write with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteADMIN() {
        assertThat(permissionEvaluator.canWrite()).isTrue();
    }

    /**
     * Check if user can write with ai creator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteAICREATOR() {
        assertThat(permissionEvaluator.canWrite()).isTrue();
    }

    /**
     * Check if user can write with aitester account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteAITESTER() {
        assertThat(permissionEvaluator.canWrite()).isFalse();
    }


    /**
     * Check if user can write project with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteProjectADMIN() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(ADMIN_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can write project with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteProjectAITESTER() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can write project with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteProjectAICREATOR() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }


    /**
     * Check if user can write project from another owner with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteOtherProjectADMIN() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can write project from another owner with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteOtherProjectAITESTER() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isFalse();
    }

    /**
     * Check if user can write project from another owner with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteOtherProjectAICREATOR() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isFalse();
    }


    /**
     * Check if user can read project with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canReadProjectADMIN() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(ADMIN_KEY));
        assertThat(permissionEvaluator.canReadProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read project with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canReadProjectAICREATOR() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read project with aitester account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canReadProjectAITESTER() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with admin account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canReadAnotherProjectADMIN() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canReadProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canReadAnotherProjectAICREATOR() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with aicreator account
     *
     * @throws Exception
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canReadAnotherProjectAITESTER() throws Exception {
        Project project = projectRepository.getOneByName(initService.getProjectName(ADMIN_KEY));
        assertThat(permissionEvaluator.canWriteProject(project.getId())).isFalse();
    }

}
