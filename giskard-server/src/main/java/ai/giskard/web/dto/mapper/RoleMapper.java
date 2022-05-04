package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Role;
import org.springframework.stereotype.Service;

import java.util.Set;
import java.util.stream.Collectors;

@Service

public class RoleMapper {
    Set<String> map(Set<Role> value) {
        return value.stream().map(Role::getName).collect(Collectors.toSet());
    }
}
