package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@UIModel
@AllArgsConstructor
@NoArgsConstructor
public class TestCatalogDTO {
    private Map<String, TestDefinitionDTO> tests;
}
