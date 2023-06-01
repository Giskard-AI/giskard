package ai.giskard.web.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;

import java.util.Map;
import java.util.UUID;

@Data
public class SuiteTestDTO {
    private Map<String, TestInputDTO> testInputs;
    private UUID testUuid;

}
