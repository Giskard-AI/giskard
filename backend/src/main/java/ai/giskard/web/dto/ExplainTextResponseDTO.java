package ai.giskard.web.dto;

import java.util.ArrayList;
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
    List<String> words = new ArrayList<String>();
    Map<String, List<Float>> weights = new HashMap<>();
}
