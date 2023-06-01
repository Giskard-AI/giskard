package ai.giskard.web.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
public class SaveTestSuiteRequestDTO {
    private String name;
    private Map<String, Map<String, String>> inputsByTestId;
}
