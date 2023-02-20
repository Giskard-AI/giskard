package ai.giskard.service.mapper;

import ai.giskard.domain.User;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import org.apache.commons.lang3.RandomStringUtils;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class UserMapperTest {

    private static final String DEFAULT_LOGIN = "johndoe";
    private static final Long DEFAULT_ID = 1L;

    @Autowired
    private GiskardMapper giskardMapper;
    private User user;
    private AdminUserDTO userDto;

    @BeforeEach
    public void init() {
        //giskardMapper = new GiskardMapperImpl();
        user = new User();
        user.setLogin(DEFAULT_LOGIN);
        user.setPassword(RandomStringUtils.random(60));
        user.setActivated(true);
        user.setEmail("johndoe@localhost");

        userDto = new AdminUserDTO(user);
    }

    @Test
    void usersToUserDTOsShouldMapOnlyNonNullUsers() {
        List<User> users = new ArrayList<>();
        users.add(user);
        users.add(null);

        List<UserDTO> userDTOS = giskardMapper.usersToUserDTOs(users);

        assertThat(userDTOS).isNotEmpty().size().isEqualTo(1);
    }

    @Test
    void userDTOsToUsersShouldMapOnlyNonNullUsers() {
        List<AdminUserDTO> usersDto = new ArrayList<>();
        usersDto.add(userDto);
        usersDto.add(null);

        List<User> users = giskardMapper.adminUserDTOsToUsers(usersDto);

        assertThat(users).isNotEmpty().size().isEqualTo(1);
    }

    @Test
    void userDTOsToUsersWithAuthoritiesStringShouldMapToUsersWithAuthoritiesDomain() {
        Set<String> authoritiesAsString = new HashSet<>();
        authoritiesAsString.add("ADMIN");
        userDto.setRoles(authoritiesAsString);

        List<AdminUserDTO> usersDto = new ArrayList<>();
        usersDto.add(userDto);

        List<User> users = giskardMapper.adminUserDTOsToUsers(usersDto);

        assertThat(users).isNotEmpty().size().isEqualTo(1);
        assertThat(users.get(0).getRoles()).isNotNull();
        assertThat(users.get(0).getRoles()).isNotEmpty();
        assertThat(users.get(0).getRoles().iterator().next().getName()).isEqualTo("ADMIN");
    }

    @Test
    void userDTOsToUsersMapWithNullAuthoritiesStringShouldReturnUserWithEmptyAuthorities() {
        userDto.setRoles(null);

        List<AdminUserDTO> usersDto = new ArrayList<>();
        usersDto.add(userDto);

        List<User> users = giskardMapper.adminUserDTOsToUsers(usersDto);

        assertThat(users).isNotEmpty().size().isEqualTo(1);
        assertThat(users.get(0).getRoles()).isNotNull();
        assertThat(users.get(0).getRoles()).isEmpty();
    }

    @Test
    void userDTOToUserMapWithAuthoritiesStringShouldReturnUserWithAuthorities() {
        Set<String> authoritiesAsString = new HashSet<>();
        authoritiesAsString.add("ADMIN");
        userDto.setRoles(authoritiesAsString);

        User user = giskardMapper.adminUserDTOtoUser(userDto);

        assertThat(user).isNotNull();
        assertThat(user.getRoles()).isNotNull();
        assertThat(user.getRoles()).isNotEmpty();
        assertThat(user.getRoles().iterator().next().getName()).isEqualTo("ADMIN");
    }

    @Test
    void userDTOToUserMapWithNullAuthoritiesStringShouldReturnUserWithEmptyAuthorities() {
        userDto.setRoles(null);

        User user = giskardMapper.adminUserDTOtoUser(userDto);

        assertThat(user).isNotNull();
        assertThat(user.getRoles()).isNotNull();
        assertThat(user.getRoles()).isEmpty();
    }

    @Test
    void userDTOToUserMapWithNullUserShouldReturnNull() {
        assertThat(giskardMapper.adminUserDTOtoUser(null)).isNull();
    }
}
