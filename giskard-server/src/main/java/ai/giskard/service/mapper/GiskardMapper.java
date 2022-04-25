package ai.giskard.service.mapper;

import ai.giskard.domain.Project;
import ai.giskard.service.dto.ml.ProjectPostDTO;
import org.mapstruct.BeanMapping;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValuePropertyMappingStrategy;

@Mapper(componentModel = "spring")
public interface GiskardMapper {
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateProjectFromDto(ProjectPostDTO dto, @MappingTarget Project entity);

    Project projectPostDTOToProject(ProjectPostDTO projectPostDto);

    ProjectPostDTO projectToProjectPostDTO(Project project);

    //User userPostDTOToUser(AdminUserDTO userPostDTO);

    //List<User> userPostDTOToUsers(List<AdminUserDTO> userPostDTOs);

}
