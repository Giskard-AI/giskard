package ai.giskard.repository;

import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
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
    default Entity getEntityType() {
        return null;
    }

    /**
     * The only goal of overriding getOne method is to mark it by @org.mapstruct.Named
     * this will allow to solve Mapstruct ambiguity between getById, getOne and getMandatoryById
     * methods when Mapstruct is looking for a I->T mapping
     */
    @Override
    @Named("no_mapstruct")
    @SuppressWarnings("all")
    @Deprecated
    T getOne(I id);

    @Override
    @Named("no_mapstruct")
    @NonNull
    T getById(@NonNull I id);

    /**
     * From <a href="https://docs.spring.io/spring-data/jpa/docs/2.6.0-RC1/reference/html/#new-features.2-5-0">Spring docs</a>:
     * <p>
     * There is a new getById method in the JpaRepository which will replace getOne, which is now deprecated.
     * Since this method returns a reference this changes the behaviour of an existing getById method which before was implemented by query derivation.
     * This in turn might lead to an unexpected LazyLoadingException when accessing attributes of that reference outside a transaction.
     * To avoid this please rename your existing getById method to getXyzById with Xyz being an arbitrary string.
     */
    @Named("no_mapstruct")
    default T getMandatoryById(I id) {
        Entity entityType = getEntityType();
        if (entityType != null) {
            return this.findById(id).orElseThrow(() -> new EntityNotFoundException(entityType, EntityNotFoundException.By.ID, id));
        }
        return findById(id).orElseThrow();
    }

    default T findOneByNullableId(I id) {
        if (id == null) {
            return null;
        }
        return getById(id);
    }
}
