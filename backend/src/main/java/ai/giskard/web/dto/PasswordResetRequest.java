package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.Email;

@Getter
@Setter
@UIModel
@AllArgsConstructor
@NoArgsConstructor
public class PasswordResetRequest {
    @Email
    String email;
}
