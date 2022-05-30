package ai.giskard.domain.ml;

import com.dataiku.j2ts.annotations.UIModel;

import java.util.List;
@UIModel
public class CodeTestCollection {
    public String title;
    public String id;
    public List<CodeTestTemplate> items;
    public short order;
}
