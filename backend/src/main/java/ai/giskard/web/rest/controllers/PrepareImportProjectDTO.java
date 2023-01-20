package ai.giskard.web.rest.controllers;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.util.Set;

@UIModel
@Getter
@Setter
@AllArgsConstructor
public class PrepareImportProjectDTO {
    private boolean conflict;
    private Set<String> loginsImportedProject;
    private Set<String> loginsCurrentInstance;
}
