package ai.giskard.web.rest.errors;

import lombok.Getter;
import org.springframework.http.HttpStatus;

public class EntityNotFoundException extends GiskardException {
    public enum By {
        NAME("name"),
        ID("id"),
        KEY("key"),
        LOGIN("login");

        @Getter
        private final String selector;

        By(String selector) {
            this.selector = selector;
        }
    }

    public EntityNotFoundException(Entity entity, Long id) {
        this(entity, By.ID, id);
    }

    public EntityNotFoundException(Entity entity, String key) {
        super(HttpStatus.NOT_FOUND, String.format("%s not found by key: %s", entity.getName(), key));
    }

    public EntityNotFoundException(Entity entity, By by, Object selector) {
        super(HttpStatus.NOT_FOUND, String.format("%s not found by %s: %s", entity.getName(), by.getSelector(), selector));
    }
}
