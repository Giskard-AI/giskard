package ai.giskard.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;

import java.io.Serializable;
import java.time.Instant;
import javax.persistence.Column;
import javax.persistence.EntityListeners;
import javax.persistence.MappedSuperclass;
import javax.persistence.Transient;

import org.springframework.data.annotation.CreatedBy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedBy;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

/**
 * Base abstract class for entities which will hold definitions for created, last modified, created by,
 * last modified by attributes.
 */
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
public abstract class AbstractAuditingEntity implements Serializable {
    // TODO andreyavtomonov (14/03/2022): remove @transient
    private static final long serialVersionUID = 1L;

    @lombok.Setter
    @lombok.Getter
    @CreatedBy
    @Column(name = "created_by", nullable = false, length = 50, updatable = false)
    @JsonIgnore
    @Transient
    private String createdBy;

    @lombok.Setter
    @lombok.Getter
    @CreatedDate
    @Column(name = "created_date", updatable = false)
    @JsonIgnore
    @Transient
    private Instant createdDate = Instant.now();

    @lombok.Setter
    @lombok.Getter
    @LastModifiedBy
    @Column(name = "last_modified_by", length = 50)
    @JsonIgnore
    @Transient
    private String lastModifiedBy;

    @lombok.Setter
    @lombok.Getter
    @LastModifiedDate
    @Column(name = "last_modified_date")
    @JsonIgnore
    @Transient
    private Instant lastModifiedDate = Instant.now();
}
