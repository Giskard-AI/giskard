package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.ml.*;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import org.mapstruct.*;

import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Mapper(componentModel = "spring",unmappedTargetPolicy = ReportingPolicy.IGNORE,
    uses = {DatasetRepository.class, ModelRepository.class})
public interface GiskardMapper {
    default Set<String> roleNames(Set<Role> value) {
        return value.stream().map(Role::getName).collect(Collectors.toSet());
    }

    default Set<Role> map(Set<String> value) {
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
    void updateProjectFromDto(ProjectPostDTO dto, @MappingTarget Project entity);

    Project projectPostDTOToProject(ProjectPostDTO projectPostDto);

    TestSuiteDTO testSuiteToTestSuiteDTO(TestSuite testSuite);

    ProjectPostDTO projectToProjectPostDTO(Project project);

    ProjectDTO projectToProjectDTO(Project project);

    List<ProjectDTO> projectsToProjectDTOs(List<Project> projects);

    List<ModelDTO> modelsToModelDTOs(List<ProjectModel> models);

    ModelDTO modelToModelDTO(ProjectModel model);

    List<DatasetDTO> datasetsToDatasetDTOs(List<Dataset> datasets);

    Dataset datasetDTOtoDataset(DatasetDTO dto);

    List<TestSuiteDTO> testSuitesToTestSuiteDTOs(List<TestSuite> testSuites);

    @Mappings({
        @Mapping(source = "testDatasetId", target = "testDataset"),
        @Mapping(source = "trainDatasetId", target = "trainDataset"),
        @Mapping(source = "modelId", target = "model")
    })
    void updateTestSuiteFromDTO(UpdateTestSuiteDTO dto, @MappingTarget TestSuite entity);

    UserDTO userToUserDTO(User user);

    default List<UserDTO> usersToUserDTOs(List<User> dtos) {
        return dtos.stream().filter(Objects::nonNull).map(this::userToUserDTO).collect(Collectors.toList());
    }

    AdminUserDTO userToAdminUserDTO(User user);

    User adminUserDTOtoUser(AdminUserDTO dto);

    default List<User> adminUserDTOsToUsers(List<AdminUserDTO> dtos) {
        return dtos.stream().filter(Objects::nonNull).map(this::adminUserDTOtoUser).collect(Collectors.toList());
    }

    User userFromId(Long id);

}
