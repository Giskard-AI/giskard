package ai.giskard.web.dto;

import ai.giskard.worker.Push;
import ai.giskard.worker.PushKind;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.stream.Collectors;

@UIModel
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PushDTO {
    private PushKind kind;
    private String key;
    private String value;
    private String pushTitle;
    private String perturbationValue;

    private List<PushDetailsDTO> details;

    public static PushDTO fromGrpc(Push push) {
        List<PushDetailsDTO> details = push.getPushDetailsList().stream().map(PushDetailsDTO::fromGrpc).collect(Collectors.toList());
        return new PushDTO(push.getKind(), push.getKey(), push.getValue(), push.getPushTitle(), push.getPerturbationValue(), details);
    }
}
