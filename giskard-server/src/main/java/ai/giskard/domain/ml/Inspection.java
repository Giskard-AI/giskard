package ai.giskard.domain.ml;


import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;

@Getter
@Setter
@Entity(name = "inspections")
public class Inspection {
    @Getter
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @ManyToOne
    private Dataset dataset;

    @ManyToOne
    private ProjectModel model;

    private String location;

    private String target;

    private String predictionTask;

//    private String inputTypes;
//
//    public Map<String, Object> getInputTypes() throws JsonProcessingException {
//        ObjectMapper objectMapper = new ObjectMapper();
//        Map<String, Object> map = objectMapper.readValue(this.inputTypes, new TypeReference<Map<String, Object>>() {
//        });
//        return map;
//    }


}
