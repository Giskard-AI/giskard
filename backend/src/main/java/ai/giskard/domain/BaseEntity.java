package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Getter;

import jakarta.persistence.*;
import java.io.Serializable;

@Getter
@MappedSuperclass
public abstract class BaseEntity implements Serializable {
    @Id
    @JsonIgnore
    @GeneratedValue
    private Long id;
}
