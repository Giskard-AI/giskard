package ai.giskard.config;

import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.repository.RoleRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.UserService;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.google.common.collect.Sets;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.Assert;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class InitService {

    private final Logger logger = LoggerFactory.getLogger(InitService.class);

    final UserRepository userRepository;

    final RoleRepository roleRepository;

    final UserService userService;

    final ProjectRepository projectRepository;

    final PasswordEncoder passwordEncoder;


    String[] mockKeys = Arrays.stream(AuthoritiesConstants.AUTHORITIES).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
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
        Arrays.stream(mockKeys).forEach(key -> {
            if (userRepository.findOneByLogin(key.toLowerCase()).isEmpty()) {
                saveUser(key, "ROLE_" + key);
            }
        });
    }

    /**
     * Initiating authorities with AuthoritiesConstants values
     */
    public void initAuthorities() {
        Arrays.stream(AuthoritiesConstants.AUTHORITIES).forEach(authName -> {
            if (roleRepository.findByName(authName).isPresent()) {
                logger.info("Authority {} already exists", authName);
                return;
            }
            Role role = new Role();
            role.setName(authName);

            roleRepository.save(role);

        });
    }

    /**
     * Registering the specified user
     *
     * @param key      key string used for identifying the user
     * @param roleName role given to the user
     * @return
     */
    private void saveUser(String key, String roleName) {
        User user = new User();
        user.setLogin(key);
        user.setEmail(String.format("%s@example.com", key.toLowerCase()));
        user.setActivated(true);
        Role role = roleRepository.findByName(roleName).orElseThrow(() -> new EntityNotFoundException(Entity.ROLE, roleName));
        user.setRoles(Sets.newHashSet(role));
        user.setPassword(passwordEncoder.encode(key).toLowerCase());
        userRepository.save(user);
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
        if (projectRepository.findOneByName(key).isEmpty()) {
            projectRepository.save(project);
        } else {
            logger.info(String.format("Project with name %s already exists", key));
        }
    }
}
