package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.security.PermissionEvaluator;
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
class PermissionTest {

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
     */
    @Test

    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void isCurrentUser() {
        assertThat(permissionEvaluator.isCurrentUser(ADMIN_KEY)).isTrue();
    }

    /**
     * Check if user is the current user with aitester account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void isCurrentUserAITESTER() {
        assertThat(permissionEvaluator.isCurrentUser(AI_TESTER_KEY)).isTrue();
    }

    /**
     * Check if user can write with admin account
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteADMIN() {
        assertThat(permissionEvaluator.canWrite()).isTrue();
    }

    /**
     * Check if user can write with ai creator account
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteAICREATOR() {
        assertThat(permissionEvaluator.canWrite()).isTrue();
    }

    /**
     * Check if user can write with aitester account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteAITESTER() {
        assertThat(permissionEvaluator.canWrite()).isFalse();
    }


    /**
     * Check if user can write project with admin account
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteProjectADMIN() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can write project with admin account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteProjectAITESTER() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can write project with aicreator account
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteProjectAICREATOR() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }


    /**
     * Check if user can write project from another owner with admin account
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canWriteOtherProjectADMIN() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can write project from another owner with admin account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canWriteOtherProjectAITESTER() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isFalse();
    }

    /**
     * Check if user can write project from another owner with aicreator account
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canWriteOtherProjectAICREATOR() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isFalse();
    }


    /**
     * Check if user can read project with aicreator account
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canReadProjectADMIN() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));
        assertThat(permissionEvaluator.canReadProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read project with aicreator account
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canReadProjectAICREATOR() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can read project with aitester account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canReadProjectAITESTER() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with admin account
     */
    @Test
    @WithMockUser(username = ADMIN_KEY, authorities = AuthoritiesConstants.ADMIN)
    void canReadAnotherProjectADMIN() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_TESTER_KEY));
        assertThat(permissionEvaluator.canReadProject(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with aicreator account
     */
    @Test
    @WithMockUser(username = AI_CREATOR_KEY, authorities = AuthoritiesConstants.AICREATOR)
    void canReadAnotherProjectAICREATOR() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(AI_CREATOR_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isTrue();
    }

    /**
     * Check if user can read another project with aicreator account
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void canReadAnotherProjectAITESTER() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));
        assertThat(permissionEvaluator.canWriteProjectId(project.getId())).isFalse();
    }

    /**
     * Check if user can read another project as a guest with the required permission
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void isGuestWithAnyRoleAsGuestWithRequiredPermission() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));

        User user = new User();
        user.setLogin(AI_TESTER_KEY);
        project.getGuests().add(user);

        assertThat(permissionEvaluator.isGuestWithAnyRole(project.getId(), AuthoritiesConstants.AITESTER)).isTrue();
    }

    /**
     * Verify than current user cannot read another project as a guest without the required permission
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void isGuestWithAnyRoleAsGuestWithoutRequiredPermission() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));

        User user = new User();
        user.setLogin(AI_TESTER_KEY);
        project.getGuests().add(user);

        assertThat(permissionEvaluator.isGuestWithAnyRole(project.getId(), AuthoritiesConstants.AICREATOR)).isFalse();
    }

    /**
     * Check if user can read another project as a guest with the required permission
     */
    @Test
    @WithMockUser(username = AI_TESTER_KEY, authorities = AuthoritiesConstants.AITESTER)
    void isGuestWithAnyRoleWithoutBeingGuestWithRequiredPermission() {
        Project project = projectRepository.getOneByName(initService.getProjectByCreatorLogin(ADMIN_KEY));

        User user = new User();
        user.setLogin(AI_CREATOR_KEY);
        project.getGuests().add(user);

        assertThat(permissionEvaluator.isGuestWithAnyRole(project.getId(), AuthoritiesConstants.AITESTER)).isFalse();
    }
}
