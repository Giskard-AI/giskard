package ai.giskard.web.rest.vm;

import lombok.Getter;
import lombok.Setter;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

/**
 * View Model object for storing a user's credentials.
 */
public class LoginVM {

    @Getter
    @Setter
    @NotNull
    @Size(min = 1, max = 50)
    private String username;

    @Setter
    @Getter
    @NotNull
    @Size(min = 4, max = 100)
    private String password;

    @Setter
    @Getter
    private boolean rememberMe;
}
