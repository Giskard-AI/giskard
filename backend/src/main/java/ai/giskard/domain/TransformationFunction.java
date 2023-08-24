package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import jakarta.persistence.DiscriminatorValue;
import jakarta.persistence.Entity;
import java.io.Serializable;

@Getter
@Entity
@DiscriminatorValue("TRANSFORMATION")
@Setter
public class TransformationFunction extends DatasetProcessFunction implements Serializable {

}
