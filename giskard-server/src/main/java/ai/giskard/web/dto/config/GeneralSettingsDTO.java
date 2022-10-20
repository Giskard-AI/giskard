package ai.giskard.web.dto.config;

import ai.giskard.domain.GeneralSettings;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.*;

@UIModel
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class GeneralSettingsDTO {
    @Getter
    @Setter
    private int externalMlWorkerEntrypointPort;

    @Getter
    @Setter
    private GeneralSettings generalSettings;
}
