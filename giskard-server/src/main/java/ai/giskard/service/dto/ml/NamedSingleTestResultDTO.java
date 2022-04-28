package ai.giskard.service.dto.ml;

import ai.giskard.worker.NamedSingleTestResult;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class NamedSingleTestResultDTO {
    private String name;
    private SingleTestResultDTO result;

    public NamedSingleTestResultDTO(NamedSingleTestResult result) {
        this.name = result.getName();
        this.result = new SingleTestResultDTO(result.getResult());
    }
}
