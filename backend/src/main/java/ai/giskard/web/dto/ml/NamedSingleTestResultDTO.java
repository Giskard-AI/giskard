package ai.giskard.web.dto.ml;

import ai.giskard.ml.dto.MLWorkerWSNamedSingleTestResultDTO;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class NamedSingleTestResultDTO {
    private String testUuid;
    private SingleTestResultDTO result;

    public NamedSingleTestResultDTO(MLWorkerWSNamedSingleTestResultDTO result) {
        this.testUuid = result.getTestUuid();
        this.result = new SingleTestResultDTO(result.getResult());
    }
}
