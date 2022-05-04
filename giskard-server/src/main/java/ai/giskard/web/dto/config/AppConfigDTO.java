package ai.giskard.web.dto.config;

import ai.giskard.web.dto.user.AdminUserDTO;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@NoArgsConstructor
@UIModel
public class AppConfigDTO {
    @Getter
    @Setter
    private AppInfoDTO app;
    @Getter
    @Setter
    private AdminUserDTO.AdminUserDTOMigration user;

    public AppConfigDTO(AppInfoDTO app, AdminUserDTO.AdminUserDTOMigration user) {
        this.app = app;
        this.user = user;
    }

    @NoArgsConstructor
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

        public AppInfoDTO(String planCode, String planName, int seatsAvailable) {
            this.planCode = planCode;
            this.planName = planName;
            this.seatsAvailable = seatsAvailable;
        }
    }
}
