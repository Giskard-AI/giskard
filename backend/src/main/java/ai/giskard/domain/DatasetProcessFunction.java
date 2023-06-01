package ai.giskard.domain;

import lombok.Getter;
import lombok.Setter;

import javax.persistence.Column;
import javax.persistence.MappedSuperclass;

@Getter
@Setter
@MappedSuperclass
public abstract class DatasetProcessFunction extends Callable {

    @Column(nullable = false)
    private boolean cellLevel;
    @Column
    private String columnType;

}
