package ai.giskard.repository;

import org.mapstruct.Named;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.NoRepositoryBean;
import org.springframework.lang.NonNullApi;

/**
 * A standard JpaRepository interface that helps Mapstruct to find an ID-to-T
 * mapper method
 */
@NoRepositoryBean
public interface MappableJpaRepository<T, ID> extends JpaRepository<T, ID> {
    /**
     * The only goal of overriding getOne method is to mark it by @org.mapstruct.Named
     * this will allow to solve Mapstruct ambiguity between getById and getOne
     * methods when Mapstruct is looking for a ID->T mapping
     */
    @Override
    @Named("_deprecated_noop_")
    @SuppressWarnings("all")
    T getOne(ID id);
}
