package ai.giskard.web.dto.config;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
@Builder
@UIModel
public class LicenseDTO {
    private String planCode;
    private String planName;
    private Integer modelLimit;
    private Integer projectLimit;
    private Integer userLimit;
    private boolean active;
}
