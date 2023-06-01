package ai.giskard.service;

import ai.giskard.domain.BaseEntity;
import ai.giskard.domain.Feedback;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Service
@Transactional
@RequiredArgsConstructor
public class ImportService {

    private final FileUploadService fileUploadService;
    private final FeedbackRepository feedbackRepository;
    private final DatasetRepository datasetRepository;
    private final ModelRepository modelRepository;
    private final UserRepository userRepository;
    private final TestSuiteRepository testSuiteRepository;
    private final FileLocationService locationService;
    private final ProjectRepository projectRepository;


    private Map<UUID, UUID> saveImportDataset(List<Dataset> datasets, Path pathToMetadataDirectory, Project savedProject) {
        Map<UUID, UUID> mapFormerNewIdDataset = new HashMap<>();
        datasets.forEach(dataset -> {
            UUID formerId = getIdFromFileName(dataset);
            Path formerDatasetPath = pathToMetadataDirectory.resolve("datasets").resolve(FileLocationService.createZSTname("data_", formerId));
            try {
                dataset.setProject(savedProject);
                FileInputStream datasetStream = new FileInputStream(formerDatasetPath.toFile());
                //Dataset savedDataset = fileUploadService.uploadDataset(savedProject, dataset, datasetStream);
                //mapFormerNewIdDataset.put(formerId, savedDataset.getId());
            } catch (IOException e) {
                throw new GiskardRuntimeException("Couldn't upload the datasets", e);
            }
        });
        return mapFormerNewIdDataset;
    }

    private Map<UUID, UUID> saveImportModel(List<ProjectModel> models, Path pathToMetadataDirectory, Project savedProject){
        Map<UUID, UUID> mapFormerNewIdModel = new HashMap<>();
        models.forEach(model -> {
            UUID formerId = getIdFromFileName(model);
            Path formerModelPath = pathToMetadataDirectory.resolve("models").resolve(FileLocationService.createZSTname("model_", formerId));
            Path formerRequirementsModelPath = pathToMetadataDirectory.resolve("models").resolve(FileLocationService.createTXTname("model-requirements_", formerId));
            try {
                model.setProject(savedProject);
                FileInputStream modelStream = new FileInputStream(formerModelPath.toFile());
                FileInputStream modelRequirementStream = new FileInputStream(formerRequirementsModelPath.toFile());
                //ProjectModel savedModel = fileUploadService.uploadModel(model, modelStream, modelRequirementStream);
                //mapFormerNewIdModel.put(formerId, savedModel.getId());
            } catch (IOException e) {
                throw new GiskardRuntimeException("Couldn't upload the models. ", e);
            }
        });
        return mapFormerNewIdModel;
    }

    private void saveImportFeedback(List<Feedback> feedbacks, Project savedProject, Map<UUID, UUID> mapFormerNewIdModel, Map<UUID, UUID> mapFormerNewIdDataset, Map<String, String> importedUsersToCurrent){
        feedbacks.forEach(feedback -> {
            feedback.setProject(savedProject);
            feedback.setDataset(datasetRepository.getById(mapFormerNewIdDataset.get(getIdFromFileName(feedback.getDataset()))));
            feedback.setModel(modelRepository.getById(mapFormerNewIdModel.get(getIdFromFileName(feedback.getModel()))));
            feedback.setUser(userRepository.getOneByLogin(importedUsersToCurrent.get(feedback.getUser().getLogin())));
            feedback.getFeedbackReplies().forEach(reply -> {
                reply.setFeedback(feedback);
                reply.setUser(userRepository.getOneByLogin(importedUsersToCurrent.get(reply.getUser().getLogin())));
            });
            feedbackRepository.save(feedback);
        });
    }

    private void saveImportTestSuites(List<TestSuite> testSuites, Project savedProject, Map<UUID, UUID> mapFormerNewIdModel, Map<UUID, UUID> mapFormerNewIdDataset){
        testSuites.forEach(testSuite -> {
            testSuite.setProject(savedProject);
            testSuite.setActualDataset(datasetRepository.getById(mapFormerNewIdDataset.get(getIdFromFileName(testSuite.getActualDataset()))));
            testSuite.setReferenceDataset(datasetRepository.getById(mapFormerNewIdDataset.get(getIdFromFileName(testSuite.getReferenceDataset()))));
            testSuite.setModel(modelRepository.getById(mapFormerNewIdModel.get(getIdFromFileName(testSuite.getModel()))));
            TestSuite savedTs = testSuiteRepository.save(testSuite);
            testSuite.getTests().forEach(test -> test.setTestSuite(savedTs));
            testSuiteRepository.save(savedTs);
        });
    }

    private Project saveImportProject(Project project, String userNameOwner, String projectKey, Map<String, String> importedUsersToCurrent){
        project.setOwner(userRepository.getOneByLogin(userNameOwner));
        project.setKey(projectKey);
        Set<User> guestList = new HashSet<>();
        importedUsersToCurrent.forEach((key, value) -> {
            if (!value.equals(userNameOwner))
                guestList.add(userRepository.getOneByLogin(value));
        });
        project.setGuests(guestList);
        return projectRepository.save(project);
    }


    Project importProject(Map<String, String> importedUsersToCurrent, String metadataDirectory, String projectKey, String userNameOwner) throws IOException{
        Path pathMetadataDirectory = Paths.get(metadataDirectory);
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory())
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        // Get back object from file
        Project project = mapper.readValue(locationService.resolvedMetadataPath(pathMetadataDirectory, Project.class.getSimpleName()).toFile(), new TypeReference<>(){});
        List<ProjectModel> models = mapper.readValue(locationService.resolvedMetadataPath(pathMetadataDirectory, ProjectModel.class.getSimpleName()).toFile(), new TypeReference<>(){} );
        List<Dataset> datasets = mapper.readValue(locationService.resolvedMetadataPath(pathMetadataDirectory, Dataset.class.getSimpleName()).toFile(), new TypeReference<>(){} );
        List<Feedback> feedbacks = mapper.readValue(locationService.resolvedMetadataPath(pathMetadataDirectory, Feedback.class.getSimpleName()).toFile(), new TypeReference<>(){} );
        List<TestSuite> testSuites = mapper.readValue(locationService.resolvedMetadataPath(pathMetadataDirectory, TestSuite.class.getSimpleName()).toFile(), new TypeReference<>(){} );
        Project savedProject = saveImportProject(project, userNameOwner, projectKey, importedUsersToCurrent);

        // Save new objects in memory
        Map<UUID, UUID> mapFormerNewIdModel = saveImportModel(models, pathMetadataDirectory, savedProject);
        Map<UUID, UUID> mapFormerNewIdDataset = saveImportDataset(datasets, pathMetadataDirectory, savedProject);
        saveImportFeedback(feedbacks, savedProject, mapFormerNewIdModel, mapFormerNewIdDataset, importedUsersToCurrent);
        saveImportTestSuites(testSuites, savedProject, mapFormerNewIdModel, mapFormerNewIdDataset);

        return projectRepository.save(savedProject);
    }

    private UUID getIdFromFileName(Object b){
        return null;
        //if (b instanceof Dataset){
        //    return Long.parseLong(((Dataset) b).getFileName().replaceFirst("data_", "").replaceFirst(".zst", ""));
        //} else if (b instanceof ProjectModel){
        //    return Long.parseLong(((ProjectModel) b).getFileName().replaceFirst("model_", "").replaceFirst(".zst", ""));
        //} else {
        //    throw new GiskardRuntimeException("Cannot get id of your entity");
        //}
    }
}
