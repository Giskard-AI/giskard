package ai.giskard.web.temp;

import ai.giskard.domain.Project;
import ai.giskard.domain.Role;
import ai.giskard.web.dto.ml.ProjectDTO;
import org.mapstruct.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.Set;
import java.util.stream.Collectors;

@Mapper(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.IGNORE)
@Service
public interface TestGiskardMapper {

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
    void updateProjectFromDto(TestProjectPostDTO dto, @MappingTarget Project entity);

    ProjectDTO projectToProjectDTO(Project project);

    TestProjectPostDTO projectToProjectPostDTO(Project project);

    @Transactional
    ProjectDTO projectToProjectDTO2(Project project);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    @Transactional
    void updateProjectFromDto2(TestProjectPostDTO dto, @MappingTarget Project entity);


}
