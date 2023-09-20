package ai.giskard.security;

import ai.giskard.service.GeneralSettingsService;
import ai.giskard.service.InitService;
import ai.giskard.web.rest.errors.GalleryDemoSpaceException;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreRemove;
import jakarta.persistence.PreUpdate;
import org.springframework.beans.factory.annotation.Configurable;

@Configurable
public class GalleryDatabaseOperationListener {
    @PrePersist
    @PreUpdate
    @PreRemove
    void beforeEntityModification(Object entity) {
        if (GeneralSettingsService.IS_RUNNING_IN_DEMO_HF_SPACES && !InitService.isUnlocked()) {
            throw new GalleryDemoSpaceException("This is a read-only Giskard Gallery instance. You cannot modify entities " + entity.getClass().getName());
        }
    }
}
