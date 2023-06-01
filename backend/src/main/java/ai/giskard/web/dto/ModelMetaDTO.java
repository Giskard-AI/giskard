package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@UIModel
public class ModelMetaDTO {
    private String id;
    private String name;
    private String model_type;
    private List<String> feature_names;
    private float classification_threshold;
    private List<String> classification_labels;
}
