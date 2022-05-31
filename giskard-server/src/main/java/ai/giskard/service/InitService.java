package ai.giskard.service;

import ai.giskard.domain.FeatureType;
import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.ModelLanguage;
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
import java.util.Arrays;
import java.util.HashMap;
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

    private final static Map<String, FeatureType> germanCreditFeatureTypes = new HashMap<>();
    private final static Map<String, FeatureType> enronFeatureTypes = new HashMap<>();
    private final static Map<String, FeatureType> zillowFeatureTypes = new HashMap<>();

    static {
        germanCreditFeatureTypes.put("account_check_status", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("duration_in_month", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("credit_history", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("purpose", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("credit_amount", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("savings", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("present_emp_since", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("installment_as_income_perc", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("sex", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("personal_status", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("other_debtors", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("present_res_since", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("property", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("age", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("other_installment_plans", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("housing", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("credits_this_bank", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("job", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("people_under_maintenance", FeatureType.NUMERIC);
        germanCreditFeatureTypes.put("telephone", FeatureType.CATEGORY);
        germanCreditFeatureTypes.put("foreign_worker", FeatureType.CATEGORY);

        enronFeatureTypes.put("Subject", FeatureType.TEXT);
        enronFeatureTypes.put("Content", FeatureType.TEXT);
        enronFeatureTypes.put("Week_day", FeatureType.CATEGORY);
        enronFeatureTypes.put("Month", FeatureType.CATEGORY);
        enronFeatureTypes.put("Hour", FeatureType.NUMERIC);
        enronFeatureTypes.put("Nb_of_forwarded_msg", FeatureType.NUMERIC);
        enronFeatureTypes.put("Year", FeatureType.NUMERIC);

        zillowFeatureTypes.put("TypeOfDewelling", FeatureType.CATEGORY);
        zillowFeatureTypes.put("BldgType", FeatureType.CATEGORY);
        zillowFeatureTypes.put("AbvGrndLivArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("Neighborhood", FeatureType.CATEGORY);
        zillowFeatureTypes.put("KitchenQual", FeatureType.CATEGORY);
        zillowFeatureTypes.put("NumGarageCars", FeatureType.NUMERIC);
        zillowFeatureTypes.put("YearBuilt", FeatureType.NUMERIC);
        zillowFeatureTypes.put("YearRemodAdd", FeatureType.NUMERIC);
        zillowFeatureTypes.put("ExterQual", FeatureType.CATEGORY);
        zillowFeatureTypes.put("LotArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("LotShape", FeatureType.CATEGORY);
        zillowFeatureTypes.put("Fireplaces", FeatureType.NUMERIC);
        zillowFeatureTypes.put("NumBathroom", FeatureType.NUMERIC);
        zillowFeatureTypes.put("Basement1Type", FeatureType.CATEGORY);
        zillowFeatureTypes.put("Basement1SurfaceArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("Basement2Type", FeatureType.CATEGORY);
        zillowFeatureTypes.put("Basement2SurfaceArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("TotalBasementArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("GarageArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("1stFlrArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("2ndFlrArea", FeatureType.NUMERIC);
        zillowFeatureTypes.put("Utilities", FeatureType.CATEGORY);
        zillowFeatureTypes.put("OverallQual", FeatureType.CATEGORY);
    }

    private final Map<String, ProjectConfig> projects = Map.of(
        "zillow", new ProjectConfig("Zillow price prediction", "aicreator",
            ModelUploadParamsDTO.builder().modelType("regression")
                .projectKey("zillow")
                .name("Zillow regression")
                .language(ModelLanguage.PYTHON)
                .languageVersion("3.7")
                .build(),
            DataUploadParamsDTO.builder()
                .projectKey("zillow")
                .name("Zillow data")
                .featureTypes(zillowFeatureTypes)
                .target("SalePrice")
                .build()
        ),
        "enron", new ProjectConfig("Enron", "aitester",
            ModelUploadParamsDTO.builder().modelType("classification")
                .classificationLabels(List.of("CALIFORNIA CRISIS", "INFLUENCE", "INTERNAL", "REGULATION"))
                .projectKey("enron")
                .name("Enron model")
                .language(ModelLanguage.PYTHON)
                .languageVersion("3.7")
                .build(),
            DataUploadParamsDTO.builder()
                .name("Enron data")
                .featureTypes(enronFeatureTypes)
                .projectKey("enron")
                .target("Target")
                .build()
        ),
        "credit", new ProjectConfig("German credit scoring", "admin",
            ModelUploadParamsDTO.builder().modelType("classification")
                .classificationLabels(List.of("Default", "Not Default"))
                .projectKey("credit")
                .name("German credit score")
                .language(ModelLanguage.PYTHON)
                .languageVersion("3.7")
                .build(),
            DataUploadParamsDTO.builder()
                .name("German Credit data")
                .projectKey("credit")
                .target("default")
                .featureTypes(germanCreditFeatureTypes)
                .build()
        )
    );

    public String getUserName(String key) {
        return users.get(key);
    }

    public String getProjectName(String key) {
        return projects.get(key).name;
    }

    public String getProjectByCreatorLogin(String login) {
        return projects.entrySet().stream().filter(e -> e.getValue().creator.equals(login)).findFirst().orElseThrow().getValue().name;
    }


    /**
     * Initializing first authorities, mock users, and mock projects
     */
    @EventListener(ApplicationReadyEvent.class)
    @Transactional
    public void init() {
        initAuthorities();
        initUsers();
        initProjects();
    }


    /**
     * Initialising users with different authorities
     */
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
        try (InputStream dsStream = dsResource.getInputStream()) {
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
        try (InputStream modelStream = modelResource.getInputStream()) {
            try (InputStream requirementsStream = requirementsResource.getInputStream()) {
                fileUploadService.uploadModel(projects.get(projectKey).modelParams, modelStream, requirementsStream);
            }
        } catch (IOException e) {
            logger.warn("Failed to upload model for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }
}
