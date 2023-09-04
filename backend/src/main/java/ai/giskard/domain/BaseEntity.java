package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import lombok.Getter;

import java.io.Serializable;

@Getter
@MappedSuperclass
public abstract class BaseEntity implements Serializable {
    @Id
    @JsonIgnore
    @GeneratedValue
    private Long id;
}
