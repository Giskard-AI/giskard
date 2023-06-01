package ai.giskard.web.dto.config;

import lombok.*;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MLWorkerConnectionInfoDTO {
    private int externalMlWorkerEntrypointPort;
    private String externalMlWorkerEntrypointHost;

    private String encryptionKey;
    private String keyId;
}
