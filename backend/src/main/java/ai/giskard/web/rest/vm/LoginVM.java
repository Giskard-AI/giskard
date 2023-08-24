package ai.giskard.web.rest.vm;

import lombok.Getter;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

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
