package ai.giskard.web.dto;

import ai.giskard.domain.ml.CodeTestCollection;
import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;
import java.util.Map;

@UIModel
@Getter
@AllArgsConstructor
public class TestTemplatesResponse {
    private List<CodeTestCollection> collections;
    private Map<String, Boolean> testAvailability;
}
