package ai.giskard.web.dto.ml;

import ai.giskard.worker.NamedSingleTestResult;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class NamedSingleTestResultDTO {
    private String name;
    private SingleTestResultDTO result;

    public NamedSingleTestResultDTO(NamedSingleTestResult result) {
        this.name = result.getName();
        this.result = new SingleTestResultDTO(result.getResult());
    }
}
