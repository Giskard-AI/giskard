package ai.giskard.web.dto.ml;

import com.dataiku.j2ts.annotations.UIModel;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Getter
@Setter
@NoArgsConstructor
@UIModel
public class InspectionDTO {
    private Long id;
    private DatasetDTO dataset;
    private ModelDTO model;
    private String name;
    private boolean sample;

    @JsonAlias("created_date")
    private Instant createdDate;
}
