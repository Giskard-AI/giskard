package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@Data
@AllArgsConstructor
@NoArgsConstructor
@UIModel
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    property = "type"
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = TestFunctionDTO.class, name = "TEST"),
    @JsonSubTypes.Type(value = SlicingFunctionDTO.class, name = "SLICE"),
    @JsonSubTypes.Type(value = TransformationFunctionDTO.class, name = "TRANSFORMATION"),
})
public class CallableDTO {
    @NotNull
    private UUID uuid;
    @NotBlank
    private String name;
    @NotBlank
    @JsonAlias("display_name")
    private String displayName;
    @UINullable
    private Integer version;
    private String module;
    private String doc;
    @JsonAlias("module_doc")
    private String moduleDoc;
    @NotNull
    private String code;
    private List<@NotBlank String> tags;
    private boolean potentiallyUnavailable;
    private List<TestFunctionArgumentDTO> args;
}
