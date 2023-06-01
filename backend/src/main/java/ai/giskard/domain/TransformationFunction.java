package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.Entity;
import javax.persistence.Table;
import javax.persistence.UniqueConstraint;
import java.io.Serializable;

@Getter
@Entity(name = "transformation_functions")
@Table(uniqueConstraints = {
    @UniqueConstraint(columnNames = {"name", "module", "version"})
})
@Setter
public class TransformationFunction extends Callable implements Serializable {

}
