package ai.giskard.domain;

import ai.giskard.utils.SimpleJSONStringAttributeConverter;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
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
    private String displayName;
    @Column(nullable = false)
    private int version;
    private String module;

    @Column(columnDefinition = "VARCHAR")
    private String doc;
    @Column(columnDefinition = "VARCHAR")
    private String moduleDoc;
    @Column(nullable = false, columnDefinition = "VARCHAR")
    private String code;
    @Column(columnDefinition = "VARCHAR")
    @Convert(converter = SimpleJSONStringAttributeConverter.class)
    private List<String> tags;

    @OneToMany(mappedBy = "testFunction", cascade = CascadeType.ALL)
    private List<TestFunctionArgument> args;

}
