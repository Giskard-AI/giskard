package ai.giskard.web.dto.config;

import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@NoArgsConstructor
@AllArgsConstructor
@UIModel
public class AppConfigDTO {
    @Getter
    @Setter
    private AppInfoDTO app;
    @Getter
    @Setter
    private AdminUserDTO user;

    @NoArgsConstructor
    @AllArgsConstructor
    public static class AppInfoDTO {
        @Getter
        @Setter
        @JsonProperty("plan_code")
        private String planCode;
        @Getter
        @Setter
        @JsonProperty("plan_name")
        private String planName;
        @Getter
        @Setter
        @JsonProperty("seats_available")
        private int seatsAvailable;

        @Getter
        @Setter
        List<RoleDTO> roles;
    }
}
