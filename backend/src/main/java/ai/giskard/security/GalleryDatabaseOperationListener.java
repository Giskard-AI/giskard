package ai.giskard.security;

import ai.giskard.service.GeneralSettingsService;
import ai.giskard.web.rest.errors.GalleryDemoSpaceException;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreRemove;
import jakarta.persistence.PreUpdate;

public class GalleryDatabaseOperationListener {
    @PrePersist
    @PreUpdate
    @PreRemove
    void beforeEntityModification(Object entity) {
        if (GeneralSettingsService.isGiskardGalleryInstance()) {
            throw new GalleryDemoSpaceException("This is a read-only Giskard Gallery instance. You cannot modify entities " + entity.getClass().getName());
        }
    }
}
