package ai.giskard.service;

import ai.giskard.config.Constants;
import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.repository.AuthorityRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.UserService;
import ai.giskard.web.rest.vm.ManagedUserVM;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.Assert;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class InitService {

    @Autowired
    UserRepository userRepository;

    @Autowired
    AuthorityRepository authorityRepository;

    @Autowired
    UserService userService;

    @Autowired
    ProjectRepository projectRepository;

    String[] mockKeys = new String[]{"ADMIN", "AITEST", "AICREATOR"};
    public Map<String, String> users = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));
    public Map<String, String> projects = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, name -> name + "Project"));

    public String getUserName(String key) {
        return users.get(key);
    }

    public String getProjectName(String key) {
        return projects.get(key);
    }

    /**
     * Initializing first authorities, mock users, and mock projects
     */
    public void init() {
        initAuthorities();
        initUsers();
        initProjects();
    }


    /**
     * Initialising users with different authorities
     */
    @Transactional
    public void initUsers() {
        Arrays.stream(mockKeys).forEach(key -> saveUser(key, "ROLE_" + key));
    }

    /**
     * Initiating authorities with AuthoritiesConstants values
     */
    public void initAuthorities() {
        Arrays.stream(AuthoritiesConstants.authorities).forEach(authName -> {
            Role role = new Role();
            role.setName(authName);
            authorityRepository.save(role);
        });
    }

    /**
     * Registering the specified user
     *
     * @param key  key string used for identifying the user
     * @param role role given to the user
     * @return
     */
    private User saveUser(String key, String role) {
        ManagedUserVM validUser = new ManagedUserVM();
        validUser.setLogin(key);
        validUser.setPassword(key);
        validUser.setFirstName(key);
        validUser.setLastName(key);
        validUser.setEmail(String.format("%s@%s", key, "giskard.ai"));
        validUser.setActivated(true);
        validUser.setImageUrl("http://placehold.it/50x50");
        validUser.setLangKey(Constants.DEFAULT_LANGUAGE);
        validUser.setRoles(Collections.singleton(role));
        return userService.registerUser(validUser, validUser.getPassword());
    }

    /**
     * Initialized with fake projects
     */
    public void initProjects() {
        Arrays.stream(mockKeys).forEach(key -> saveProject(key + "Project", key));
    }

    /**
     * Save project
     *
     * @param key        key used to easily identify the project
     * @param ownerLogin login of the owner
     */
    private void saveProject(String key, String ownerLogin) {
        User owner = userRepository.getOneByLogin(ownerLogin.toLowerCase());
        Assert.notNull(owner, "Owner does not exist in database");
        Project project = new Project(key, key, key, owner);
        projectRepository.save(project);
    }
}
