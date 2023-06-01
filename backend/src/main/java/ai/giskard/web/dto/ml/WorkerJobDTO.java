package ai.giskard.web.dto.ml;

import ai.giskard.domain.MLWorkerType;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Date;

@Getter
@Setter
@NoArgsConstructor
public class WorkerJobDTO {

    private Date executionDate = new Date();
    @UINullable
    private Date completionDate;
    private MLWorkerType mlWorkerType;
}
