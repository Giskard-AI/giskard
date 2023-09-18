package ai.giskard.web.dto.config;

import lombok.*;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MLWorkerConnectionInfoDTO {
    private String instanceId;
    private String serverVersion;
    private String user;
    private String instanceLicenseId;
}
