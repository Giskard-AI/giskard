package ai.giskard.web.dto.config;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@UIModel
@Getter
@Setter
@NoArgsConstructor
public class MLWorkerInfoDTO {
    @Getter
    @Setter
    @NoArgsConstructor
    public static class PlatformInfoDTO {
        private String machine;
        private String node;
        private String processor;
        private String release;
        private String system;
        private String version;
    }

    private PlatformInfoDTO platform;
    private String interpreter;
    private String interpreterVersion;
    private Map<String, String> installedPackages;
    private int internalGrpcPort;
    private boolean isRemote;
    private int pid;
    private long processStartTime;
}
