package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.web.dto.ml.*;
import ai.giskard.web.dto.ml.write.TestSuitePostDTO;
import org.mapstruct.*;

import java.util.List;

@Mapper(componentModel = "spring",unmappedTargetPolicy = ReportingPolicy.IGNORE,
    uses = {RoleMapper.class, RoleDTOMapper.class})
public interface GiskardMapper {
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

    List<TestSuiteDTO> testSuitesToTestSuiteDTOs(List<TestSuite> testSuites);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateTestSuiteFromDTO(TestSuitePostDTO dto, @MappingTarget TestSuite entity);


}
