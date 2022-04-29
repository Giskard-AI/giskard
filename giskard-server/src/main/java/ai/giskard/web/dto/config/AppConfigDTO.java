package ai.giskard.web.dto.config;

import ai.giskard.web.dto.user.AdminUserDTO;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@NoArgsConstructor
public class AppConfigDTO {
    @Getter
    @Setter
    private AppInfoDTO app;
    @Getter
    @Setter
    private AdminUserDTO user;

    public AppConfigDTO(AppInfoDTO app, AdminUserDTO.AdminUserDTOMigration user) {
        this.app = app;
        this.user = user;
    }

    @NoArgsConstructor
    public static class AppInfoDTO {
        @Getter
        @Setter
        private String planCode;
        @Getter
        @Setter
        private String planName;
        @Getter
        @Setter
        private int seatsAvailable;

        public AppInfoDTO(String planCode, String planName, int seatsAvailable) {
            this.planCode = planCode;
            this.planName = planName;
            this.seatsAvailable = seatsAvailable;
        }
        //plan_code: "basic"
        //plan_name: "Basic Plan"
        //seats_available: 1

    }
}
