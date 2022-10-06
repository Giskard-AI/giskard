package ai.giskard.domain;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.config.SpringContext;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class InspectionSettings {
   private Integer limeNumberSamples = SpringContext.getBean(ApplicationProperties.class).getLimeNumberSamples(); 
}
