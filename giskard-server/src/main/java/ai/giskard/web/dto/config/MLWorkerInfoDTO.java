package ai.giskard.web.dto.config;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.NoArgsConstructor;

import java.util.Map;

@NoArgsConstructor
@UIModel
public class MLWorkerInfoDTO {
    @NoArgsConstructor
    public static class PlatformInfoDTO {
        public String machine;
        public String node;
        public String processor;
        public String release;
        public String system;
        public String version;
    }

    public PlatformInfoDTO platform;
    public String interpreter;
    public String interpreterVersion;
    public Map<String, String> installedPackages;
    public int internalGrpcPort;
    public boolean isRemote;
    public int pid;
    public long processStartTime;
}
