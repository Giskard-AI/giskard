package ai.giskard.web.dto.mapper;

import ai.giskard.domain.*;
import ai.giskard.domain.ml.*;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.utils.JSON;
import ai.giskard.web.dto.*;
import ai.giskard.web.dto.ml.*;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import org.mapstruct.*;

import java.util.*;
import java.util.stream.Collectors;

@Mapper(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.ERROR,
    uses = {
        DatasetRepository.class,
        ModelRepository.class,
        ProjectRepository.class,
        JSON.class
    }
)
public interface GiskardMapper {
    default Set<String> roleNames(Set<Role> value) {
        return value.stream().map(Role::getName).collect(Collectors.toSet());
    }

    default Set<Role> stringSetToRoleSet(Set<String> value) {
        if (value == null) {
            return Collections.emptySet();
        }
        return value.stream().map(roleName -> {
            Role role = new Role();
            role.setName(roleName);
            return role;
        }).collect(Collectors.toSet());
    }

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    @Mapping(target = "datasets", ignore = true)
    @Mapping(target = "feedbacks", ignore = true)
    @Mapping(target = "guests", ignore = true)
    @Mapping(target = "models", ignore = true)
    @Mapping(target = "owner", ignore = true)
    @Mapping(target = "mlWorkerType", ignore = true)
    void updateProjectFromDto(ProjectPostDTO dto, @MappingTarget Project entity);

    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    @Mapping(target = "datasets", ignore = true)
    @Mapping(target = "feedbacks", ignore = true)
    @Mapping(target = "guests", ignore = true)
    @Mapping(target = "models", ignore = true)
    @Mapping(target = "owner", ignore = true)
    @Mapping(target = "mlWorkerType", ignore = true)
    Project projectPostDTOToProject(ProjectPostDTO projectPostDto);

    ProjectPostDTO projectToProjectPostDTO(Project project);

    ProjectDTO projectToProjectDTO(Project project);

    List<ProjectDTO> projectsToProjectDTOs(List<Project> projects);

    List<ModelDTO> modelsToModelDTOs(List<ProjectModel> models);

    @Mapping(source = "classificationLabels", target = "classificationLabels")
    @Mapping(source = "featureNames", target = "featureNames")
    ModelDTO modelToModelDTO(ProjectModel model);

    List<DatasetDTO> datasetsToDatasetDTOs(List<Dataset> datasets);

    @Mapping(source = "columnMeanings", target = "columnMeanings")
    DatasetDTO datasetToDatasetDTO(Dataset dataset);

    UserDTO userToUserDTO(User user);

    default List<UserDTO> usersToUserDTOs(List<User> dtos) {
        return dtos.stream().filter(Objects::nonNull).map(this::userToUserDTO).toList();
    }

    InspectionDTO toDTO(Inspection inspection);

    AdminUserDTO userToAdminUserDTO(User user);

    @Mapping(target = "activationKey", ignore = true)
    @Mapping(target = "password", ignore = true)
    @Mapping(target = "projects", ignore = true)
    @Mapping(target = "resetDate", ignore = true)
    @Mapping(target = "resetKey", ignore = true)
    User adminUserDTOtoUser(AdminUserDTO dto);

    default List<User> adminUserDTOsToUsers(List<AdminUserDTO> dtos) {
        return dtos.stream().filter(Objects::nonNull).map(this::adminUserDTOtoUser).toList();
    }

    @Mapping(source = "classificationLabels", target = "classificationLabels")
    @Mapping(source = "featureNames", target = "featureNames")
    ModelMetadataDTO modelToModelMetadataDTO(ProjectModel model);

    @Mapping(source = "projectId", target = "project")
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    ProjectModel fromDTO(ModelDTO dto);

    @Mapping(source = "columnMeanings", target = "columnMeanings")
    @Mapping(target = "inspections", ignore = true)
    @Mapping(target = "project", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    Dataset fromDTO(DatasetDTO dto);

    @Mapping(target = "message", source = "feedbackMessage")
    @Mapping(target = "projectId", source = "project.id")
    PrepareDeleteDTO.LightFeedback toDTO(Feedback obj);

    List<PrepareDeleteDTO.LightFeedback> toLightFeedbacks(List<Feedback> obj);

    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "project", source = "projectKey")
    @Mapping(target = "executions", ignore = true)
    TestSuiteNew fromDTO(TestSuiteNewDTO dto);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "suite", ignore = true)
    @Mapping(target = "executions", ignore = true)
    SuiteTest fromDTO(SuiteTestDTO dto);

    @AfterMapping
    default void afterMapping(@MappingTarget TestSuiteNew suite) {
        suite.getTests().forEach(e -> e.setSuite(suite));
    }

    @AfterMapping
    default void afterMapping(@MappingTarget SuiteTest test) {
        test.getTestInputs().forEach(e -> e.setTest(test));
    }

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "test", ignore = true)
    @Mapping(target = "alias", source = "alias")
    TestInput fromDTO(TestInputDTO dto);
    TestInputDTO toDTO(TestInput obj);


    List<TestSuiteNewDTO> toDTO(List<TestSuiteNew> suites);

    @Mapping(target = "projectKey", source = "project.key")
    TestSuiteNewDTO toDTO(TestSuiteNew suite);

    default Map<String, TestInputDTO> map(List<TestInput> value) {
        return value.stream().collect(Collectors.toMap(TestInput::getName, this::toDTO));
    }

    default List<TestInput> map(Map<String, TestInputDTO> value) {
        return value.values().stream().map(this::fromDTO).toList();
    }

    @Mapping(target = "suiteId", source = "suite.id")
    TestSuiteExecutionDTO toDto(TestSuiteExecution save);

    List<TestSuiteExecutionDTO> testSuiteExecutionToDTOs(List<TestSuiteExecution> save);

    List<WorkerJobDTO> workerJobsToDTOs(List<? extends WorkerJob> workerJobs);

}
