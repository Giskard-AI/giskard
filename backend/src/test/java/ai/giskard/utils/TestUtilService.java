package ai.giskard.utils;

import ai.giskard.domain.User;
import ai.giskard.security.AuthoritiesConstants;
import ai.giskard.service.UserService;
import ai.giskard.web.dto.user.AdminUserDTO;
import org.apache.commons.lang3.RandomStringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class TestUtilService {
    @Autowired
    private UserService userService;

    public User createAdminUser() {
        AdminUserDTO.AdminUserDTOWithPassword user = new AdminUserDTO.AdminUserDTOWithPassword();
        user.setLogin("login_" + RandomStringUtils.randomAlphabetic(5));
        user.setPassword("password_" + RandomStringUtils.random(5));
        user.setEmail(RandomStringUtils.randomAlphabetic(5) + "@giskard.com");
        user.setRoles(Set.of(AuthoritiesConstants.ADMIN));
        return userService.createUser(user);
    }
}
