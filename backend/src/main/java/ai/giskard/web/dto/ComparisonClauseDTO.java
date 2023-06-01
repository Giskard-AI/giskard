package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Data
@UIModel
public class ComparisonClauseDTO {

    @NotBlank
    private String columnName;
    @NotNull
    private ComparisonType comparisonType;
    @NotNull
    private String columnDtype;
    @UINullable
    private String value;

}
