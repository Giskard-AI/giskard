package ai.giskard.web.rest.errors;

import lombok.Getter;

public class EntityNotFoundException extends BadRequestAlertException { //NOSONAR
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
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by key: %s", entity.getName(), key), entity.name().toLowerCase(), "entitynotfound");
    }

    public EntityNotFoundException(Entity entity, By by, Object selector) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not found by %s: %s", entity.getName(), by.getSelector(), selector), entity.name().toLowerCase(), "entitynotfound");
    }
}
