package ai.giskard.domain;

import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import lombok.Getter;
import lombok.Setter;

import javax.persistence.*;
import java.util.List;
import java.util.UUID;

@Getter
@Entity(name = "test_functions")
@Table(uniqueConstraints={
    @UniqueConstraint(columnNames = {"name", "module", "version"})
})
@Setter
public class TestFunction {

    @Id
    private UUID uuid;
    @Column(nullable = false)
    private String name;
    @Column(nullable = false)
    private int version;
    private String module;
    private String doc;
    private String moduleDoc;
    @Column(nullable = false)
    private String code;
    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<String> tags;
}
