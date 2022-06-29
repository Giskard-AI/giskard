package ai.giskard.web.dto.config;

import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.RoleDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.util.List;

@NoArgsConstructor
@AllArgsConstructor
@UIModel
@Builder
public class AppConfigDTO {
    @Getter
    @Setter
    private AppInfoDTO app;
    @Getter
    @Setter
    private AdminUserDTO user;

    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    @Getter
    @Setter
    public static class AppInfoDTO {
        private String planCode;
        private String planName;
        private int seatsAvailable;
        private List<RoleDTO> roles;
        private String giskardVersion;
    }
}
