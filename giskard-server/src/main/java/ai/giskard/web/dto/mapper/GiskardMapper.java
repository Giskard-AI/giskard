package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Project;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.dto.ml.ProjectDTO;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

import java.util.List;

@Mapper(componentModel = "spring")
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


}
