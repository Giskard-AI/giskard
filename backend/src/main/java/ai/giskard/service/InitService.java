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
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.Assert;

import java.io.IOException;
import java.io.InputStream;
import java.util.*;
import java.util.stream.Collectors;

import static java.util.Arrays.stream;

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
    public static final String ZILLOW_PROJECT_KEY = "zillow";
    public static final String ENRON_PROJECT_KEY = "enron";
    public static final String GERMAN_CREDIT_PROJECT_KEY = "credit";

    public static final String OBJECT = "object";

    public static final String INT_64 = "int64";

    public static final String FLOAT_64 = "float64";

    static {
        germanCreditColumnTypes.put("account_check_status", OBJECT);
        germanCreditColumnTypes.put("duration_in_month", INT_64);
        germanCreditColumnTypes.put("credit_history", OBJECT);
        germanCreditColumnTypes.put("purpose", OBJECT);
        germanCreditColumnTypes.put("credit_amount", INT_64);
        germanCreditColumnTypes.put("savings", OBJECT);
        germanCreditColumnTypes.put("present_emp_since", OBJECT);
        germanCreditColumnTypes.put("installment_as_income_perc", INT_64);
        germanCreditColumnTypes.put("sex", OBJECT);
        germanCreditColumnTypes.put("personal_status", OBJECT);
        germanCreditColumnTypes.put("other_debtors", OBJECT);
        germanCreditColumnTypes.put("present_res_since", INT_64);
        germanCreditColumnTypes.put("property", OBJECT);
        germanCreditColumnTypes.put("age", INT_64);
        germanCreditColumnTypes.put("other_installment_plans", OBJECT);
        germanCreditColumnTypes.put("housing", OBJECT);
        germanCreditColumnTypes.put("credits_this_bank", INT_64);
        germanCreditColumnTypes.put("job", OBJECT);
        germanCreditColumnTypes.put("people_under_maintenance", INT_64);
        germanCreditColumnTypes.put("telephone", OBJECT);
        germanCreditColumnTypes.put("foreign_worker", OBJECT);

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


        enronColumnTypes.put("Subject", OBJECT);
        enronColumnTypes.put("Content", OBJECT);
        enronColumnTypes.put("Week_day", OBJECT);
        enronColumnTypes.put("Year", FLOAT_64);
        enronColumnTypes.put("Month", OBJECT);
        enronColumnTypes.put("Hour", FLOAT_64);
        enronColumnTypes.put("Nb_of_forwarded_msg", FLOAT_64);

        enronFeatureTypes.put("Subject", FeatureType.TEXT);
        enronFeatureTypes.put("Content", FeatureType.TEXT);
        enronFeatureTypes.put("Week_day", FeatureType.CATEGORY);
        enronFeatureTypes.put("Month", FeatureType.CATEGORY);
        enronFeatureTypes.put("Hour", FeatureType.NUMERIC);
        enronFeatureTypes.put("Nb_of_forwarded_msg", FeatureType.NUMERIC);
        enronFeatureTypes.put("Year", FeatureType.NUMERIC);

        zillowColumnTypes.put("TypeOfDewelling", OBJECT);
        zillowColumnTypes.put("BldgType", OBJECT);
        zillowColumnTypes.put("AbvGrndLivArea", INT_64);
        zillowColumnTypes.put("Neighborhood", OBJECT);
        zillowColumnTypes.put("KitchenQual", OBJECT);
        zillowColumnTypes.put("NumGarageCars", INT_64);
        zillowColumnTypes.put("YearBuilt", INT_64);
        zillowColumnTypes.put("YearRemodAdd", INT_64);
        zillowColumnTypes.put("ExterQual", OBJECT);
        zillowColumnTypes.put("LotArea", INT_64);
        zillowColumnTypes.put("LotShape", OBJECT);
        zillowColumnTypes.put("Fireplaces", INT_64);
        zillowColumnTypes.put("NumBathroom", INT_64);
        zillowColumnTypes.put("Basement1Type", OBJECT);
        zillowColumnTypes.put("Basement1SurfaceArea", INT_64);
        zillowColumnTypes.put("Basement2Type", OBJECT);
        zillowColumnTypes.put("Basement2SurfaceArea", INT_64);
        zillowColumnTypes.put("TotalBasementArea", INT_64);
        zillowColumnTypes.put("GarageArea", INT_64);
        zillowColumnTypes.put("1stFlrArea", INT_64);
        zillowColumnTypes.put("2ndFlrArea", INT_64);
        zillowColumnTypes.put("Utilities", OBJECT);
        zillowColumnTypes.put("OverallQual", INT_64);

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
    private Map<String, ProjectConfig> projects;
    String[] mockKeys = stream(AuthoritiesConstants.AUTHORITIES).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
    private final Map<String, String> users = stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));

    private Map<String, ProjectConfig> createProjectConfigMap() {
        return Map.of(
            ZILLOW_PROJECT_KEY, new ProjectConfig("House Pricing Regression", "aicreator",
                ModelUploadParamsDTO.builder().modelType("regression")
                    .projectKey(ZILLOW_PROJECT_KEY)
                    .name("House Pricing Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(zillowFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .projectKey(ZILLOW_PROJECT_KEY)
                    .name("House Pricing Data")
                    .featureTypes(zillowFeatureTypes)
                    .columnTypes(zillowColumnTypes)
                    .target("SalePrice")
                    .build(),
                new InspectionSettings()
            ),
            ENRON_PROJECT_KEY, new ProjectConfig("Email Classification", "aitester",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("CALIFORNIA CRISIS", "INFLUENCE", "INTERNAL", "REGULATION"))
                    .projectKey(ENRON_PROJECT_KEY)
                    .name("Email Classification Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(enronFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("Email data")
                    .featureTypes(enronFeatureTypes)
                    .columnTypes(enronColumnTypes)
                    .projectKey(ENRON_PROJECT_KEY)
                    .target("Target")
                    .build(),
                new InspectionSettings(5)
            ),
            GERMAN_CREDIT_PROJECT_KEY, new ProjectConfig("Credit Scoring Classification", "admin",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("Default", "Not default"))
                    .projectKey(GERMAN_CREDIT_PROJECT_KEY)
                    .name("Credit Scoring Model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(germanCreditFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("Credit Scoring data")
                    .projectKey(GERMAN_CREDIT_PROJECT_KEY)
                    .target("default")
                    .featureTypes(germanCreditFeatureTypes)
                    .columnTypes(germanCreditColumnTypes)
                    .build(),
                new InspectionSettings()
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
        projects = createProjectConfigMap();
        generalSettingsService.saveIfNotExists(new GeneralSettings());
        initAuthorities();
        initUsers();
        initProjects();
    }

    /**
     * Initialising users with different authorities
     */
    public void initUsers() {
        stream(mockKeys).forEach(key -> {
            if (userRepository.findOneByLogin(key.toLowerCase()).isEmpty()) {
                saveUser(key, "ROLE_" + key);
            }
        });
    }

    /**
     * Initiating authorities with AuthoritiesConstants values
     */
    public void initAuthorities() {
        stream(AuthoritiesConstants.AUTHORITIES).forEach(authName -> {
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
        logger.info("Creating demo projects");
        projects.forEach((key, config) -> {
            try {
                saveProject(key, config.creator);
            } catch (IOException e) {
                logger.error("Project with key %s not saved".formatted(key), e);
            }
        });
    }

    /**
     * Save project
     *
     * @param projectKey    project key used to easily identify the project
     * @param ownerUserName login of the owner
     */
    private void saveProject(String projectKey, String ownerUserName) throws IOException {
        if (projectRepository.findOneByKey(projectKey).isEmpty()) {
            String projectName = projects.get(projectKey).name;
            String ownerLogin = ownerUserName.toLowerCase();
            User owner = userRepository.getOneByLogin(ownerLogin);
            Assert.notNull(owner, "Owner does not exist in database");
            Project project = new Project(projectKey, projectName, projectName, owner);
            project.setMlWorkerType(MLWorkerType.INTERNAL);
            project.setInspectionSettings(projects.get(projectKey).inspectionSettings);
            projectService.create(project, ownerLogin);
            projectRepository.save(project);
            List<String> models = getFileNames(projectKey, "models");
            models.forEach(e -> uploadModel(projectKey, e));
            List<String> datasets = getFileNames(projectKey, "datasets");
            datasets.forEach(e -> uploadDataframe(projectKey, e));
            logger.info("Created project: {}", projectName);
        } else {
            logger.info("Project with key {} already exists", projectKey);
        }
    }

    /**
     * Get the list of file keys
     * This necessary when calling from jar
     *
     * @param projectKey key of the project
     * @param type       type (models/datasets)
     * @return List of names
     */
    private List<String> getFileNames(String projectKey, String type) throws IOException {
        String path = PROJECTDIR + projectKey + "/" + type + "/*";
        PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
        return Arrays.stream(resolver.getResources(path)).map(e -> Objects.requireNonNull(e.getFilename())
            .substring(0, e.getFilename().indexOf("."))).toList();
    }

    private void uploadDataframe(String projectKey, String fileName) {
        ProjectConfig config = projects.get(projectKey);
        Project project = projectRepository.getOneByKey(projectKey);
        String path = CLASSPATH + PROJECTDIR + projectKey + "/datasets/" + fileName + ".csv.zst";
        Resource dsResource = resourceLoader.getResource(path);
        try (InputStream dsStream = dsResource.getInputStream()) {
            DataUploadParamsDTO dsParams = config.datasetParams;
            String target = fileName.contains("prod") ? null : dsParams.getTarget();
            fileUploadService.uploadDataset(
                project,
                dsParams.getName() + " " + fileName,
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
        // hacky way to override features list, we should rely on project export/import in the future to handle demo projects
        if (ENRON_PROJECT_KEY.equals(projectKey) && "pytorch_bert".equals(filename)) {
            modelDTO.setFeatureNames(Lists.newArrayList("Content"));
        }
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

                fileUploadService.uploadModel(modelDTOCopy, modelStream, requirementsStream);
            }
        } catch (IOException e) {
            logger.warn("Failed to upload model for demo project {}", projectKey);
            throw new RuntimeException(e);
        }
    }

    private record ProjectConfig(String name, String creator, ModelUploadParamsDTO modelParams,
                                 DataUploadParamsDTO datasetParams, InspectionSettings inspectionSettings) {
    }
}
