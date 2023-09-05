package ai.giskard.security;

import ai.giskard.service.InitService;
import ai.giskard.web.rest.errors.GalleryDemoSpaceException;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreRemove;
import jakarta.persistence.PreUpdate;
import org.springframework.beans.factory.annotation.Configurable;
import org.springframework.beans.factory.annotation.Value;

@Configurable
public class GalleryDatabaseOperationListener {
    @Value("${GISKARD_DEMO_SPACE}")
    boolean isGiskardGalleryInstance;

    @PrePersist
    @PreUpdate
    @PreRemove
    void beforeEntityModification(Object entity) {
        if (isGiskardGalleryInstance && InitService.isInitialized()) {
            throw new GalleryDemoSpaceException("This is a read-only Giskard Gallery instance. You cannot modify entities " + entity.getClass().getName());
        }
    }
}
