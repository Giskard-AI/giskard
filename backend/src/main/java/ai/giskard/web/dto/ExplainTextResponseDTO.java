package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ExplainTextResponseDTO {
    List<String> words = new ArrayList<>();
    Map<String, List<Float>> weights = new HashMap<>();
}
