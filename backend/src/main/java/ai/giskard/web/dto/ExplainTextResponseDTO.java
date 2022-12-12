package ai.giskard.web.dto;

import java.util.HashMap;
import java.util.Map;

import com.dataiku.j2ts.annotations.UIModel;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class ExplainTextResponseDTO {
    Map<String, List<Map<String, Float>>> explanations = new HashMap<>(); 
}
