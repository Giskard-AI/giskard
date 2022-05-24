package ai.giskard.service;

import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.RoleRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.web.dto.DataUploadParamsDTO;
import ai.giskard.web.dto.ModelUploadParamsDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import com.google.common.collect.Sets;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.Assert;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.List;
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
    final ProjectService projectService;

    final PasswordEncoder passwordEncoder;
    private final ResourceLoader resourceLoader;
    private final FileUploadService fileUploadService;

    private record ProjectConfig(String name, String creator, ModelUploadParamsDTO modelParams,
                                 DataUploadParamsDTO datasetParams) {
    }

    String[] mockKeys = Arrays.stream(AuthoritiesConstants.AUTHORITIES).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
    public Map<String, String> users = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));
    private Map<String, ProjectConfig> projects = Map.of(
        "zillow",
        new ProjectConfig("Zillow price prediction", "AICREATOR",
            ModelUploadParamsDTO.builder().modelType("regression")
                .projectKey("zillow")
                .name("Zillow regression")
                .build(),
            DataUploadParamsDTO.builder()
                .projectKey("enron")
                .target("Target")
                .build()
        ),
        "enron", new ProjectConfig("Enron", "AITESTER",
            ModelUploadParamsDTO.builder().modelType("classification")
                .classificationLabels(List.of("a", "b", "c")) // TODO andreyavtomonov (24/05/2022): add real labels
                .projectKey("enron")
                .name("Enron model")
                .build(),
            DataUploadParamsDTO.builder()
                .projectKey("enron")
                .target("Target")
                .build()
        ),
        "credit", new ProjectConfig("German credit scoring", "ADMIN",
            ModelUploadParamsDTO.builder().modelType("classification")
                .classificationLabels(List.of("Default", "Not Default"))
                .projectKey("credit")
                .name("German credit score")
                .build(),
            DataUploadParamsDTO.builder()
                .projectKey("enron")
                .target("Target")
                .build()
        )
    );
    //public Map<String, String> projects = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, name -> String.format("%s's project", StringUtils.capitalize(name.toLowerCase()))));


    public String getUserName(String key) {
        return users.get(key);
    }

    public String getProjectName(String key) {
        return projects.get(key).name;
    }


    /**
     * Initializing first authorities, mock users, and mock projects
     */
    @EventListener(ApplicationReadyEvent.class)
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
        user.setLogin(key.toLowerCase());
        user.setEmail(String.format("%s@example.com", key.toLowerCase()));
        user.setActivated(true);
        Role role = roleRepository.findByName(roleName).orElseThrow(() -> new EntityNotFoundException(Entity.ROLE, roleName));
        user.setRoles(Sets.newHashSet(role));
        user.setPassword(passwordEncoder.encode(key.toLowerCase()));
        user.setEnabled(true);
        user.setActivated(true);
        userRepository.save(user);
    }

    /**
     * Initialized with default projects
     */
    @Transactional
    public void initProjects() {
        projects.forEach((key, config) -> saveProject(key, config.creator));
    }

    /**
     * Save project
     *
     * @param projectKey    project key used to easily identify the project
     * @param ownerUserName login of the owner
     */
    private void saveProject(String projectKey, String ownerUserName) {
        String projectName = projects.get(projectKey).name;
        String ownerLogin = ownerUserName.toLowerCase();
        User owner = userRepository.getOneByLogin(ownerLogin);
        Assert.notNull(owner, "Owner does not exist in database");
        Project project = new Project(projectKey, projectName, projectName, owner);
        if (projectRepository.findOneByName(projectName).isEmpty()) {
            projectService.create(project, ownerLogin);
            projectRepository.save(project);
            uploadModel(projectKey);
            uploadDataframe(projectKey);
        } else {
            logger.info(String.format("Project with name %s already exists", projectName));
        }
    }

    private void uploadDataframe(String projectKey) {
        ProjectConfig config = projects.get(projectKey);
        Project project = projectRepository.getOneByKey(projectKey);
        Resource dsResource = resourceLoader.getResource("classpath:demo_projects/" + projectKey + "/dataset.csv.zst");
        try (InputStream dsStream = Files.newInputStream(dsResource.getFile().toPath())) {
            DataUploadParamsDTO dsParams = config.datasetParams;
            fileUploadService.uploadDataset(
                project,
                dsParams.getName(),
                dsParams.getFeatureTypes(),
                dsParams.getTarget(),
                dsStream
            );
        } catch (IOException e) {
            logger.warn("Failed to upload dataset for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }

    private void uploadModel(String projectKey) {
        Resource modelResource = resourceLoader.getResource("classpath:demo_projects/" + projectKey + "/model.pkl.zst");
        Resource requirementsResource = resourceLoader.getResource("classpath:demo_projects/" + projectKey + "/requirements.txt");
        try (InputStream modelStream = Files.newInputStream(modelResource.getFile().toPath())) {
            try (InputStream requirementsStream = Files.newInputStream(requirementsResource.getFile().toPath())) {
                fileUploadService.uploadModel(projects.get(projectKey).modelParams, modelStream, requirementsStream);
            }
        } catch (IOException e) {
            logger.warn("Failed to upload model for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }
}
