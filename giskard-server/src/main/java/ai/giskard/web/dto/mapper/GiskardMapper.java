package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.utils.JSON;
import ai.giskard.web.dto.ModelMetadataDTO;
import ai.giskard.web.dto.TestSuiteCreateDTO;
import ai.giskard.web.dto.ml.*;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import org.mapstruct.*;

import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Set;
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
    @Mapping(target = "testSuites", ignore = true)
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
    @Mapping(target = "testSuites", ignore = true)
    Project projectPostDTOToProject(ProjectPostDTO projectPostDto);

    TestSuiteDTO testSuiteToTestSuiteDTO(TestSuite testSuite);

    ProjectPostDTO projectToProjectPostDTO(Project project);

    ProjectDTO projectToProjectDTO(Project project);

    List<ProjectDTO> projectsToProjectDTOs(List<Project> projects);

    List<ModelDTO> modelsToModelDTOs(List<ProjectModel> models);

    @Mapping(source = "classificationLabels", target = "classificationLabels")
    @Mapping(source = "featureNames", target = "featureNames")
    ModelDTO modelToModelDTO(ProjectModel model);

    List<DatasetDTO> datasetsToDatasetDTOs(List<Dataset> datasets);

    @Mapping(source = "featureTypes", target = "featureTypes")
    DatasetDTO datasetToDatasetDTO(Dataset dataset);

    List<TestSuiteDTO> testSuitesToTestSuiteDTOs(List<TestSuite> testSuites);

    @Mapping(source = "testDatasetId", target = "testDataset")
    @Mapping(source = "trainDatasetId", target = "trainDataset")
    @Mapping(source = "modelId", target = "model")
    @Mapping(target = "project", ignore = true)
    @Mapping(target = "tests", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    void updateTestSuiteFromDTO(UpdateTestSuiteDTO dto, @MappingTarget TestSuite entity);

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

    @Mapping(source = "modelId", target = "model")
    @Mapping(source = "trainDatasetId", target = "trainDataset")
    @Mapping(source = "testDatasetId", target = "testDataset")
    @Mapping(source = "projectId", target = "project")
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "tests", ignore = true)
    @Mapping(target = "createdBy", ignore = true)
    @Mapping(target = "createdDate", ignore = true)
    @Mapping(target = "lastModifiedBy", ignore = true)
    @Mapping(target = "lastModifiedDate", ignore = true)
    TestSuite fromDTO(TestSuiteCreateDTO dto);
}
