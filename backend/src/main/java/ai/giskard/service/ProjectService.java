package ai.giskard.service;


import ai.giskard.domain.*;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.exception.EntityAlreadyExistsException;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.ee.LicenseService;
import ai.giskard.utils.ArtifactUtils;
import ai.giskard.utils.LicenseUtils;
import ai.giskard.utils.YAMLConverter;
import ai.giskard.utils.ZipUtils;
import ai.giskard.web.dto.PrepareImportProjectDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.stereotype.Service;
import org.springframework.util.FileSystemUtils;
import org.springframework.web.multipart.MultipartFile;

import jakarta.validation.constraints.NotNull;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ProjectService {
    private final LicenseService licenseService;
    private final UserRepository userRepository;
    private final ProjectRepository projectRepository;
    private final FileLocationService locationService;
    private final TaskScheduler giskardTaskScheduler;
    private final ImportService importService;
    private final TestSuiteService testSuiteService;
    private final SlicingFunctionRepository slicingFunctionRepository;
    private final TransformationFunctionRepository transformationFunctionRepository;

    final GiskardMapper giskardMapper;

    private final Logger log = LoggerFactory.getLogger(ProjectService.class);

    public static final Pattern PROJECT_KEY_PATTERN = Pattern.compile("^[a-z\\d_]+$");

    /**
     * Update project
     *
     * @param id         id of the project to update
     * @param projectDTO updated project
     * @return project updated
     */
    public Project update(@NotNull Long id, ProjectPostDTO projectDTO) {
        Project project = projectRepository.getMandatoryById(id);
        giskardMapper.updateProjectFromDto(projectDTO, project);
        return projectRepository.save(project);
    }

    public static boolean isProjectKeyValid(String projectKey) {
        return PROJECT_KEY_PATTERN.matcher(projectKey).matches();
    }

    private void validateProjectKey(String projectKey) {
        if (!isProjectKeyValid(projectKey)) {
            throw new IllegalArgumentException(String.format("Project key %s is not valid. Project keys can contain lower case latin characters, digits and underscores", projectKey));
        }
    }

    /**
     * Create project
     */
    public Project create(Project project, String ownerLogin) {
        String projectKey = project.getKey();
        validateProjectKey(projectKey);

        if (LicenseUtils.isLimitReached(licenseService.getCurrentLicense().getProjectLimit(), (int) projectRepository.count())) {
            throw new GiskardRuntimeException("Project limit is reached. You can upgrade your plan to create more.");
        }

        projectRepository.findOneByKey(projectKey).ifPresent(p -> {
            throw new EntityAlreadyExistsException(String.format("Project with key %s already exists", projectKey));
        });
        User owner = userRepository.getOneByLogin(ownerLogin);
        project.setOwner(owner);
        return projectRepository.save(project);
    }

    /**
     * Test if the authenticated user is in the guestlist
     *
     * @param userList list of users
     * @return boolean
     */
    public boolean isUserInGuestList(Set<User> userList) {
        return userList.stream().anyMatch(guest -> guest.getLogin().equals(SecurityUtils.getCurrentAuthenticatedUserLogin()));
    }

    /**
     * Delete the project
     *
     * @param id id of the project to delete
     */
    public void delete(Long id) {
        Project project = projectRepository.getMandatoryById(id);
        try {
            projectRepository.deleteById(id);
            projectRepository.flush();
            FileSystemUtils.deleteRecursively(locationService.resolvedProjectHome(project.getKey()));
        } catch (Exception e) {
            throw new GiskardRuntimeException("Failed to delete project %s".formatted(project.getKey()));
        }
    }

    public byte[] export(Long id) throws IOException {
        Path projectZipPath = null;
        Path temporaryExportDir = null;
        Project project = projectRepository.getMandatoryById(id);
        // Create a tmp folder

        // Get the project from repository
        Path homeProject = locationService.resolvedProjectHome(project.getKey());
        try {
            temporaryExportDir = locationService.temporaryMetadataDirectory("project_export-" + project.getKey());
            Files.createDirectories(temporaryExportDir);

            Set<TestFunction> testFunctions = ArtifactUtils.getAllReferencedTestFunction(project);
            Set<UUID> slicingFunctionUuids = ArtifactUtils.getAllReferencedTestInput(project, "SlicingFunction");
            Set<UUID> transformationFunctionUuids = ArtifactUtils.getAllReferencedTestInput(project, "TransformationFunction");

            createMetadataYamlFiles(temporaryExportDir, project, testFunctions, slicingFunctionUuids, transformationFunctionUuids);

            // Copy content of the /giskard-home/projects/{projecKey} into the temporary newly created folder
            try {
                FileSystemUtils.copyRecursively(homeProject, temporaryExportDir);

                Path globalSource = locationService.globalPath();
                ArtifactUtils.copyAllArtifactFolders(globalSource.resolve("tests"), temporaryExportDir.resolve("tests"),
                    testFunctions.stream().map(TestFunction::getUuid).collect(Collectors.toSet()));
                ArtifactUtils.copyAllArtifactFolders(globalSource.resolve("slices"), temporaryExportDir.resolve("slices"), slicingFunctionUuids);
                ArtifactUtils.copyAllArtifactFolders(globalSource.resolve("transformations"), temporaryExportDir.resolve("transformations"), transformationFunctionUuids);
            } catch (IOException e) {
                throw new GiskardRuntimeException("Error while copying your project for export", e);
            }

            // Zip the project and send it as bytes to the Frontend
            projectZipPath = locationService.resolvedTmpPath().resolve(String.format("%s.zip", project.getKey()));
            if (!Files.exists(projectZipPath)) {
                Files.createFile(projectZipPath);
            }
            ZipUtils.zip(temporaryExportDir, projectZipPath);

            return Files.readAllBytes(projectZipPath);
        } finally {
            if (projectZipPath != null) {
                FileSystemUtils.deleteRecursively(projectZipPath);
            }
            if (temporaryExportDir != null) {
                FileSystemUtils.deleteRecursively(temporaryExportDir);
            }
        }
    }

    public void createMetadataYamlFiles(Path temporaryExportDirectory, Project project, Set<TestFunction> testFunctions,
                                        Set<UUID> slicingFunctionUuids, Set<UUID> transformationFunctionUuids) throws IOException {
        // Convert every part of the project into YAML files stored into the created folder
        Path projectMetadataPath = locationService.resolvedMetadataPath(temporaryExportDirectory, Project.class.getSimpleName());
        Path modelsMetadatPath = locationService.resolvedMetadataPath(temporaryExportDirectory, ProjectModel.class.getSimpleName());
        Path datasetsMetadataPath = locationService.resolvedMetadataPath(temporaryExportDirectory, Dataset.class.getSimpleName());
        Path testFunctionMetadataPath = testSuiteService.resolvedMetadataPath(temporaryExportDirectory, TestFunction.class.getSimpleName());
        Path slicingFunctionMetadataPath = testSuiteService.resolvedMetadataPath(temporaryExportDirectory, SlicingFunction.class.getSimpleName());
        Path transformationFunctionMetadataPath = testSuiteService.resolvedMetadataPath(temporaryExportDirectory, TransformationFunction.class.getSimpleName());
        Path feedBacksMetadataPath = locationService.resolvedMetadataPath(temporaryExportDirectory, Feedback.class.getSimpleName());
        Path testSuiteMetadataPath = testSuiteService.resolvedMetadataPath(temporaryExportDirectory, TestSuite.class.getSimpleName());

        YAMLConverter.exportEntityToYAML(project, projectMetadataPath);
        YAMLConverter.exportEntitiesToYAML(project.getModels(), modelsMetadatPath);
        YAMLConverter.exportEntitiesToYAML(project.getDatasets(), datasetsMetadataPath);

        YAMLConverter.exportEntitiesToYAML(testFunctions, testFunctionMetadataPath);
        YAMLConverter.exportEntitiesToYAML(slicingFunctionRepository.findAllById(slicingFunctionUuids), slicingFunctionMetadataPath);
        YAMLConverter.exportEntitiesToYAML(transformationFunctionRepository.findAllById(transformationFunctionUuids), transformationFunctionMetadataPath);

        YAMLConverter.exportEntitiesToYAML(project.getFeedbacks(), feedBacksMetadataPath);
        YAMLConverter.exportEntitiesToYAML(project.getTestSuites(), testSuiteMetadataPath);
    }

    public Path unzipProject(MultipartFile zipFile) throws IOException {
        Path pathToTimestampDirectory = locationService.temporaryMetadataDirectory("project_import-" + zipFile.getOriginalFilename());
        if (!Files.exists(pathToTimestampDirectory)) {
            ZipUtils.unzipProjectFile(zipFile, pathToTimestampDirectory);
        }
        scheduleTemporaryDirectoryDeletion(pathToTimestampDirectory);
        return pathToTimestampDirectory;
    }

    private void scheduleTemporaryDirectoryDeletion(Path pathToTimestampDirectory) {
        giskardTaskScheduler.schedule(() -> {
            if (!Files.exists(pathToTimestampDirectory)) {
                return;
            }
            log.info("Deleting a temporary directory for an abandoned project import: {}", pathToTimestampDirectory);
            try {
                FileSystemUtils.deleteRecursively(pathToTimestampDirectory);
            } catch (IOException e) {
                log.error("Failed to delete temporary directory {}", pathToTimestampDirectory, e);
            }
        }, Instant.now().plus(1, ChronoUnit.HOURS));
    }

    public PrepareImportProjectDTO prepareImport(MultipartFile zipFile) throws IOException {
        Project project;
        List<Feedback> feedbacks;
        Path pathToMetadataDirectory = null;
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory())
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        try {
            pathToMetadataDirectory = unzipProject(zipFile);
            project = mapper.readValue(locationService.resolvedMetadataPath(pathToMetadataDirectory, Project.class.getSimpleName()).toFile(), new TypeReference<>() {
            });
            feedbacks = mapper.readValue(locationService.resolvedMetadataPath(pathToMetadataDirectory, Feedback.class.getSimpleName()).toFile(), new TypeReference<>() {
            });
        } catch (IOException e) {
            FileSystemUtils.deleteRecursively(pathToMetadataDirectory);
            throw new GiskardRuntimeException("Error while preparing your project import", e);
        }
        String projectKey = project.getKey();
        boolean projectKeyAlreadyExists = projectRepository.findOneByKey(projectKey).isPresent();

        // Get the set of every user that participated to feedbacks (reply or feedback post)
        Set<String> loginsImportedProject = new TreeSet<>() {
        };
        feedbacks.forEach(feedback -> {
            loginsImportedProject.add(feedback.getUser().getLogin());
            feedback.getFeedbackReplies().forEach(reply -> loginsImportedProject.add(reply.getUser().getLogin()));
        });

        // Get the set of every user in the instance of giskard
        List<User> currentUsers = userRepository.findAllByEnabled(true);
        Set<String> loginsCurrentInstance = new TreeSet<>();
        currentUsers.forEach(user -> loginsCurrentInstance.add(user.getLogin()));

        return new PrepareImportProjectDTO(projectKeyAlreadyExists, loginsImportedProject, loginsCurrentInstance, projectKey, pathToMetadataDirectory.toString());
    }

    public Project importProject(Map<String, String> importedUsersToCurrent, String metadataDirectory, String projectKey, String userNameOwner) throws IOException {
        Path tmpDir = Paths.get(metadataDirectory);
        if (!Files.exists(tmpDir)) {
            throw new GiskardRuntimeException("Temporary directory containing the project contents not found. Try re-importing it.");
        }
        try {
            return importService.importProject(importedUsersToCurrent, metadataDirectory, projectKey, userNameOwner);
        } catch (Exception e) {
            throw new GiskardRuntimeException("Error while importing the project", e);
        } finally {
            FileSystemUtils.deleteRecursively(tmpDir);
        }
    }


    /**
     * Uninvite user from project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return update project
     */
    public Project uninvite(Long id, Long userId) {
        User user = userRepository.getMandatoryById(userId);
        Project project = projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.removeGuest(user);
        projectRepository.save(project);
        return project;
    }

    /**
     * Inviting user to the project guestlist
     *
     * @param id     id of the project
     * @param userId id of the user
     * @return updated project
     */
    public Project invite(Long id, Long userId) {
        User user = userRepository.getMandatoryById(userId);
        Project project = projectRepository.findOneWithGuestsById(id).orElseThrow(() -> new EntityNotFoundException(Entity.PROJECT, id));
        project.addGuest(user);
        projectRepository.save(project);
        return project;
    }

    /**
     * Listing projects accessible by the user
     * Handling access control
     *
     * @return list of projects
     */
    public List<Project> list() {
        String username = SecurityUtils.getCurrentAuthenticatedUserLogin().toLowerCase();
        User user = userRepository.findOneByLogin(username).orElseThrow(() -> new NotInDatabaseException(Entity.USER, username));
        List<Project> projects;
        if (SecurityUtils.isCurrentUserAdmin()) {
            projects = projectRepository.findAll();
        } else {
            projects = projectRepository.getProjectsByOwnerOrGuestsContains(user, user);
        }
        return projects;
    }
}
