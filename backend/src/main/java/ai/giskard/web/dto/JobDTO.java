package ai.giskard.web.dto;

import ai.giskard.domain.MLWorkerType;
import ai.giskard.jobs.JobState;
import ai.giskard.jobs.JobType;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Date;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@UIModel
public class JobDTO {

    private Date scheduledDate;
    @UINullable
    private JobState state;
    private Float progress;
    private long projectId;
    private JobType jobType;
    private MLWorkerType mlWorkerType;
}
