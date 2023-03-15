package ai.giskard.web.dto.config;

import ai.giskard.service.ee.FeatureFlag;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

import java.time.Instant;
import java.util.Map;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
@Builder
@UIModel
public class LicenseDTO {
    private String planCode;
    private String planName;
    private Integer projectLimit;
    private Integer userLimit;
    private boolean active;
    private String licenseProblem;
    private Instant expiresOn;
    private Map<FeatureFlag, Boolean> features;
}
