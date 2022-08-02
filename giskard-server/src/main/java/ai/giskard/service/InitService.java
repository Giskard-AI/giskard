package ai.giskard.service;

import ai.giskard.domain.*;
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

    private static final Map<String, FeatureType> germanCreditFeatureTypes = new HashMap<>();
    private static final Map<String, String> germanCreditColumnTypes = new HashMap<>();
    private static final Map<String, FeatureType> enronFeatureTypes = new HashMap<>();
    private static final Map<String, String> enronColumnTypes = new HashMap<>();
    private static final Map<String, FeatureType> zillowFeatureTypes = new HashMap<>();
    private static final Map<String, String> zillowColumnTypes = new HashMap<>();
    private static final String CLASSPATH = "classpath:";
    private static final String PROJECTDIR = "demo_projects/";

    static {
        germanCreditColumnTypes.put("account_check_status", "object");
        germanCreditColumnTypes.put("duration_in_month", "int64");
        germanCreditColumnTypes.put("credit_history", "object");
        germanCreditColumnTypes.put("purpose", "object");
        germanCreditColumnTypes.put("credit_amount", "int64");
        germanCreditColumnTypes.put("savings", "object");
        germanCreditColumnTypes.put("present_emp_since", "object");
        germanCreditColumnTypes.put("installment_as_income_perc", "int64");
        germanCreditColumnTypes.put("sex", "object");
        germanCreditColumnTypes.put("personal_status", "object");
        germanCreditColumnTypes.put("other_debtors", "object");
        germanCreditColumnTypes.put("present_res_since", "int64");
        germanCreditColumnTypes.put("property", "object");
        germanCreditColumnTypes.put("age", "int64");
        germanCreditColumnTypes.put("other_installment_plans", "object");
        germanCreditColumnTypes.put("housing", "object");
        germanCreditColumnTypes.put("credits_this_bank", "int64");
        germanCreditColumnTypes.put("job", "object");
        germanCreditColumnTypes.put("people_under_maintenance", "int64");
        germanCreditColumnTypes.put("telephone", "object");
        germanCreditColumnTypes.put("foreign_worker", "object");

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


        enronColumnTypes.put("Subject", "object");
        enronColumnTypes.put("Content", "object");
        enronColumnTypes.put("Week_day", "object");
        enronColumnTypes.put("Year", "float64");
        enronColumnTypes.put("Month", "object");
        enronColumnTypes.put("Hour", "float64");
        enronColumnTypes.put("Nb_of_forwarded_msg", "float64");

        enronFeatureTypes.put("Subject", FeatureType.TEXT);
        enronFeatureTypes.put("Content", FeatureType.TEXT);
        enronFeatureTypes.put("Week_day", FeatureType.CATEGORY);
        enronFeatureTypes.put("Month", FeatureType.CATEGORY);
        enronFeatureTypes.put("Hour", FeatureType.NUMERIC);
        enronFeatureTypes.put("Nb_of_forwarded_msg", FeatureType.NUMERIC);
        enronFeatureTypes.put("Year", FeatureType.NUMERIC);

        zillowColumnTypes.put("TypeOfDewelling", "object");
        zillowColumnTypes.put("BldgType", "object");
        zillowColumnTypes.put("AbvGrndLivArea", "int64");
        zillowColumnTypes.put("Neighborhood", "object");
        zillowColumnTypes.put("KitchenQual", "object");
        zillowColumnTypes.put("NumGarageCars", "int64");
        zillowColumnTypes.put("YearBuilt", "int64");
        zillowColumnTypes.put("YearRemodAdd", "int64");
        zillowColumnTypes.put("ExterQual", "object");
        zillowColumnTypes.put("LotArea", "int64");
        zillowColumnTypes.put("LotShape", "object");
        zillowColumnTypes.put("Fireplaces", "int64");
        zillowColumnTypes.put("NumBathroom", "int64");
        zillowColumnTypes.put("Basement1Type", "object");
        zillowColumnTypes.put("Basement1SurfaceArea", "int64");
        zillowColumnTypes.put("Basement2Type", "object");
        zillowColumnTypes.put("Basement2SurfaceArea", "int64");
        zillowColumnTypes.put("TotalBasementArea", "int64");
        zillowColumnTypes.put("GarageArea", "int64");
        zillowColumnTypes.put("1stFlrArea", "int64");
        zillowColumnTypes.put("2ndFlrArea", "int64");
        zillowColumnTypes.put("Utilities", "object");
        zillowColumnTypes.put("OverallQual", "int64");

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

    final UserRepository userRepository;
    final RoleRepository roleRepository;
    final UserService userService;
    final ProjectRepository projectRepository;
    final ProjectService projectService;
    final PasswordEncoder passwordEncoder;
    private final Logger logger = LoggerFactory.getLogger(InitService.class);
    private final GeneralSettingsService generalSettingsService;
    private final ResourceLoader resourceLoader;
    private final FileUploadService fileUploadService;
    private final Map<String, ProjectConfig> projects = createProjectConfigMap();
    String[] mockKeys = Arrays.stream(AuthoritiesConstants.AUTHORITIES).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
    private final Map<String, String> users = Arrays.stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));

    private Map<String, ProjectConfig> createProjectConfigMap() {
        String zillowProjectKey = "zillow";
        String enronProjectKey = "enron";
        String germanCreditProjectKey = "credit";

        return Map.of(
            zillowProjectKey, new ProjectConfig("House Pricing Regression", "aicreator",
                ModelUploadParamsDTO.builder().modelType("regression")
                    .projectKey(zillowProjectKey)
                    .name("House Pricing Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .build(),
                DataUploadParamsDTO.builder()
                    .projectKey(zillowProjectKey)
                    .name("House Pricing Data")
                    .featureTypes(zillowFeatureTypes)
                    .columnTypes(zillowColumnTypes)
                    .target("SalePrice")
                    .build()
            ),
            enronProjectKey, new ProjectConfig("Email Classification", "aitester",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("CALIFORNIA CRISIS", "INFLUENCE", "INTERNAL", "REGULATION"))
                    .projectKey(enronProjectKey)
                    .name("Email Classification Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("Email data")
                    .featureTypes(enronFeatureTypes)
                    .columnTypes(enronColumnTypes)
                    .projectKey(enronProjectKey)
                    .target("Target")
                    .build()
            ),
            germanCreditProjectKey, new ProjectConfig("Credit Scoring Classification", "admin",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("Default", "Not default"))
                    .projectKey(germanCreditProjectKey)
                    .name("Credit Scoring Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("Credit Scoring data")
                    .projectKey(germanCreditProjectKey)
                    .target("default")
                    .featureTypes(germanCreditFeatureTypes)
                    .columnTypes(germanCreditColumnTypes)
                    .build()
            )
        );
    }

    public String getUserName(String key) {
        return users.get(key);
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
        generalSettingsService.saveIfNotExists(new GeneralSettings());
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
            logger.info("Project with key {} already exists", projectKey);
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
                dsParams.getColumnTypes(), target,
                dsStream
            );
        } catch (IOException e) {
            logger.warn("Failed to upload dataset for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }

    private void uploadModel(String projectKey, String filename) {
        ProjectConfig config = projects.get(projectKey);
        String pathToModel = CLASSPATH + PROJECTDIR + projectKey + "/models/" + filename + ".model.pkl.zst";
        String pathToRequirements = CLASSPATH + PROJECTDIR + projectKey + "/requirements/" + filename + ".requirements.txt";
        Resource modelResource = resourceLoader.getResource(pathToModel);
        Resource requirementsResource = resourceLoader.getResource(pathToRequirements);
        ModelUploadParamsDTO modelDTO = projects.get(projectKey).modelParams;
        ModelUploadParamsDTO modelDTOCopy = ModelUploadParamsDTO.builder().modelType(modelDTO.getModelType())
            .projectKey(modelDTO.getProjectKey())
            .name(config.modelParams.getName() + " " + filename)
            .language(modelDTO.getLanguage())
            .languageVersion(modelDTO.getLanguageVersion())
            .featureNames(modelDTO.getFeatureNames())
            .classificationLabels(modelDTO.getClassificationLabels())
            .build();
        try (InputStream modelStream = modelResource.getInputStream()) {
            try (InputStream requirementsStream = requirementsResource.getInputStream()) {
                fileUploadService.uploadModel(projects.get(projectKey).modelParams, modelStream, requirementsStream);
            }
        } catch (IOException e) {
            logger.warn("Failed to upload model for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }

    private record ProjectConfig(String name, String creator, ModelUploadParamsDTO modelParams,
                                 DataUploadParamsDTO datasetParams) {
    }
}
