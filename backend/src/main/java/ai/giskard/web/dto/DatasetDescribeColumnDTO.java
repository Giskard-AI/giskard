package ai.giskard.web.dto;

import lombok.Data;

@Data
public class DatasetDescribeColumnDTO {
    private String columnName;
    private int count;
    private int unique;
    private String top;
    private long freq;
}
