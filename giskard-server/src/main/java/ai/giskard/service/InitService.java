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
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
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
    String[] mockKeys = stream(AuthoritiesConstants.AUTHORITIES).map(key -> key.replace("ROLE_", "")).toArray(String[]::new);
    private final Map<String, String> users = stream(mockKeys).collect(Collectors.toMap(String::toLowerCase, String::toLowerCase));

    private Map<String, ProjectConfig> createProjectConfigMap() {
        String zillowProjectKey = "zillow";
        String enronProjectKey = "enron";
        String germanCreditProjectKey = "credit";

        return Map.of(
            zillowProjectKey, new ProjectConfig("Zillow price prediction", "aicreator",
                ModelUploadParamsDTO.builder().modelType("regression")
                    .projectKey(zillowProjectKey)
                    .name("Zillow regression")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(zillowFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .projectKey(zillowProjectKey)
                    .name("Zillow data")
                    .featureTypes(zillowFeatureTypes)
                    .columnTypes(zillowColumnTypes)
                    .target("SalePrice")
                    .build()
            ),
            enronProjectKey, new ProjectConfig("Enron", "aitester",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("CALIFORNIA CRISIS", "INFLUENCE", "INTERNAL", "REGULATION"))
                    .projectKey(enronProjectKey)
                    .name("Enron model")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(enronFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("Enron data")
                    .featureTypes(enronFeatureTypes)
                    .columnTypes(enronColumnTypes)
                    .projectKey(enronProjectKey)
                    .target("Target")
                    .build()
            ),
            germanCreditProjectKey, new ProjectConfig("German credit scoring", "admin",
                ModelUploadParamsDTO.builder().modelType("classification")
                    .classificationLabels(List.of("Default", "Not default"))
                    .projectKey(germanCreditProjectKey)
                    .name("German credit score")
                    .language(ModelLanguage.PYTHON)
                    .languageVersion("3.7")
                    .featureNames(germanCreditFeatureTypes.keySet().stream().toList())
                    .build(),
                DataUploadParamsDTO.builder()
                    .name("German Credit data")
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
     * @throws IOException
     */
    private List<String> getFileNames(String projectKey, String type) throws IOException {
        String path = PROJECTDIR + projectKey + "/" + type + "/*";
        PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
        return Arrays.stream(resolver.getResources(path)).map(e -> e.getFilename().substring(0, e.getFilename().indexOf("."))).toList();
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
        String pathToModel = CLASSPATH + PROJECTDIR + projectKey + "/models/" + filename + ".model.pkl.zst";
        String pathToRequirements = CLASSPATH + PROJECTDIR + projectKey + "/requirements/" + filename + ".requirements.txt";
        Resource modelResource = resourceLoader.getResource(pathToModel);
        Resource requirementsResource = resourceLoader.getResource(pathToRequirements);
        ModelUploadParamsDTO modelDTO = projects.get(projectKey).modelParams;
        ModelUploadParamsDTO modelDTOCopy = ModelUploadParamsDTO.builder().modelType(modelDTO.getModelType())
            .projectKey(modelDTO.getProjectKey())
            .name(modelDTO.getProjectKey() + " model " + filename)
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
                                 DataUploadParamsDTO datasetParams) {
    }
}
