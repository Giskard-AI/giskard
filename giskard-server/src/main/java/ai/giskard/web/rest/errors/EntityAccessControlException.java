package ai.giskard.web.rest.errors;


public class EntityAccessControlException extends BadRequestAlertException {


    public EntityAccessControlException(Entity entity, Long id) {
        super(ErrorConstants.DEFAULT_TYPE, String.format("%s not accessible by id: %d", entity.getName(), id), entity.name().toLowerCase(), "accesscontrolerror", "");
    }
}
