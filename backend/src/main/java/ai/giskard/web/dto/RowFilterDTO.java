package ai.giskard.web.dto;

import ai.giskard.domain.ml.table.Filter;
import com.dataiku.j2ts.annotations.UIModel;
import com.dataiku.j2ts.annotations.UINullable;
import lombok.Data;

import java.util.List;

@UIModel
@Data
public class RowFilterDTO {
    @UINullable
    private Filter filter;
    @UINullable
    private List<ColumnFilterDTO> columnFilters;
    @UINullable
    private int[] removeRows;
}
