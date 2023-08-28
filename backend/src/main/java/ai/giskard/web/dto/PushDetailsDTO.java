package ai.giskard.web.dto;


//import ai.giskard.worker.CallToActionKind;
//import ai.giskard.worker.PushDetails;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@UIModel
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class PushDetailsDTO {
    public String action;
    public String explanation;
    public String button;
    //public CallToActionKind kind;

    //public static PushDetailsDTO fromGrpc(PushDetails details) {
    //    return new PushDetailsDTO(details.getAction(), details.getExplanation(), details.getButton(), details.getCta());
    //}
}
