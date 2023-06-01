package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

@Data
public class DatasetDescribeColumnDTO {
    private String columnName;
    private int count;
    @UINullable
    private Integer unique;
    @UINullable
    private String top;
    @UINullable
    private Long freq;
    @UINullable
    private Float mean;
    @UINullable
    private Float std;
    @UINullable
    private Float min;
    @UINullable
    private Float twentyFive;
    @UINullable
    private Float fifty;
    @UINullable
    private Float seventyFive;
    @UINullable
    private Float max;
}
