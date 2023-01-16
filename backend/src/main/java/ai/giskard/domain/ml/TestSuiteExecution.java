package ai.giskard.domain.ml;

import ai.giskard.domain.BaseEntity;
import ai.giskard.utils.JSONStringAttributeConverter;
import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.ml.SingleTestResultDTO;
import com.fasterxml.jackson.core.type.TypeReference;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

@Entity
@NoArgsConstructor
@Getter
@Setter
public class TestSuiteExecution extends BaseEntity {

    @Converter
    public static class SingleTestResultConverter extends JSONStringAttributeConverter<Map<String, SingleTestResultDTO>> {
        @Override
        public TypeReference<Map<String, SingleTestResultDTO>> getValueTypeRef() {
            return new TypeReference<>() {
            };
        }
    }

    @ManyToOne
    TestSuiteNew suite;
    Date executionDate = new Date();

    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private Map<String, String> inputs;

    @Enumerated(EnumType.STRING)
    TestResult result;

    @OneToMany(mappedBy = "execution", cascade = CascadeType.ALL)
    private List<SuiteTestExecution> results = new ArrayList<>();

    // TODO: add status for job in progress

    // TODO: add information (run duration, error message)

    public TestSuiteExecution(TestSuiteNew suite) {
        this.suite = suite;
    }
}
