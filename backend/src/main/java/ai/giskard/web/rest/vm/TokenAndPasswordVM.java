package ai.giskard.web.rest.vm;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * View Model object for storing the user's key and password.
 */
@UIModel
@Getter
@Setter
@NoArgsConstructor
public class TokenAndPasswordVM {
    private String token;
    private String newPassword;
}
