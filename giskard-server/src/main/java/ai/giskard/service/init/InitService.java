package ai.giskard.service.init;

import ai.giskard.config.Constants;
import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.repository.AuthorityRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.UserService;
import ai.giskard.service.UsernameAlreadyUsedException;
import ai.giskard.web.rest.vm.ManagedUserVM;
import org.hibernate.exception.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.Assert;

import java.util.Arrays;
import java.util.Collections;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class InitService {

    private final Logger logger = LoggerFactory.getLogger(InitService.class);

    final UserRepository userRepository;

    final AuthorityRepository authorityRepository;

    final UserService userService;

    final ProjectRepository projectRepository;

    String[] mockKeys = Arrays.stream(AuthoritiesConstants.authorities).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
    public Map<String, String> users = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));
    public Map<String, String> projects = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, name -> name + "Project"));

    public InitService(UserRepository userRepository, AuthorityRepository authorityRepository, UserService userService, ProjectRepository projectRepository) {
        this.userRepository = userRepository;
        this.authorityRepository = authorityRepository;
        this.userService = userService;
        this.projectRepository = projectRepository;
    }

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
            if (authorityRepository.findByName(authName).isPresent()) {
                logger.info("Authority {} already exists", authName);
                return;
            }
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
    private void saveUser(String key, String role) {
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
        try {
            userService.registerUser(validUser, validUser.getPassword());
        } catch (UsernameAlreadyUsedException | ConstraintViolationException e) {
            logger.info("User with name {} already exists", key);
        }
    }

    /**
     * Initialized with default projects
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
        try {
            projectRepository.save(project);
        } catch (Exception e) {
            logger.info(String.format("Project with name %s already exists", key));
        }
    }
}
