package ai.giskard.web.dto.config;

import ai.giskard.domain.GeneralSettings;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.time.Instant;
import java.util.List;

@NoArgsConstructor
@AllArgsConstructor
@Setter
@Builder
@UIModel
public class AppConfigDTO {
    @Getter
    @Setter
    private AppInfoDTO app;
    @Getter
    @Setter
    private AdminUserDTO user;

    @Getter
    @Setter
    private LicenseDTO license;

    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Setter
    @Getter
    public static class AppInfoDTO {
        private String planCode;
        private String planName;
        private int seatsAvailable;
        private List<RoleDTO> roles;
        private String version;
        private String buildBranch;
        private String buildCommitId;
        private Instant buildCommitTime;
        private GeneralSettings generalSettings;
        private String hfSpaceId;
        @JsonProperty(value = "isRunningOnHfSpaces")
        private boolean isRunningOnHfSpaces;
        @JsonProperty(value = "isDemoHfSpace")
        private boolean isDemoHfSpace;
    }
}
