package ai.giskard.ml.tunnel;

import io.netty.buffer.ByteBuf;
import lombok.AllArgsConstructor;
import lombok.Getter;

@AllArgsConstructor
@Getter
public class DecryptionResult {
    private String keyId;
    private ByteBuf data;
}
