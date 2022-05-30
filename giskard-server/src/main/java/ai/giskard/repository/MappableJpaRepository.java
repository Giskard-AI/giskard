package ai.giskard.repository;

import lombok.NonNull;
import org.mapstruct.Named;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.NoRepositoryBean;

/**
 * A standard JpaRepository interface that helps Mapstruct to find an ID-to-T
 * mapper method
 */
@NoRepositoryBean
public interface MappableJpaRepository<T, I> extends JpaRepository<T, I> {
    /**
     * The only goal of overriding getOne method is to mark it by @org.mapstruct.Named
     * this will allow to solve Mapstruct ambiguity between getById and getOne
     * methods when Mapstruct is looking for a I->T mapping
     */
    @Override
    @Named("_noop_")
    @SuppressWarnings("all")
    T getOne(I id);

    @Override
    @Named("_noop_")
    @NonNull
    T getById(@NonNull I id);

    default T findOneByNullableId(I id) {
        if (id == null) {
            return null;
        }
        return getById(id);
    }
}
