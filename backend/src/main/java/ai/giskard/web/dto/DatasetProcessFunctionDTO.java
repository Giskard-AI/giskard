package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@NoArgsConstructor
public class DatasetProcessFunctionDTO extends CallableDTO {
    private boolean cellLevel;
    @UINullable
    private String columnType;
    private DatasetProcessFunctionType processType;
    private List<Map<String, Object>> clauses;
    private Set<String> projectKeys = new HashSet<>();
}
