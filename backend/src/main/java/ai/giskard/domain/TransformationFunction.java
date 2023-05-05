package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;
import java.io.Serializable;

@Getter
@Entity
@DiscriminatorValue("TRANSFORMATION")
@Setter
public class TransformationFunction extends DatasetProcessFunction implements Serializable {

}
