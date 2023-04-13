package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.Entity;
import javax.persistence.Table;
import javax.persistence.UniqueConstraint;
import java.io.Serializable;

@Getter
@Entity(name = "slice_functions")
@Table(uniqueConstraints = {
    @UniqueConstraint(columnNames = {"name", "module", "version"})
})
@Setter
public class SliceFunction extends Callable implements Serializable {
    
}
