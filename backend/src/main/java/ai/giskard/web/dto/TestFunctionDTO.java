package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@AllArgsConstructor
@UIModel
public class TestFunctionDTO extends CallableDTO {
    @JsonAlias("debug_description")
    private String debugDescription;
}
