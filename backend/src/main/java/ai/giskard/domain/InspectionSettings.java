package ai.giskard.domain;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.config.SpringContext;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class InspectionSettings implements Serializable{
   private Integer limeNumberSamples = SpringContext.getBean(ApplicationProperties.class).getLimeNumberSamples();
}
