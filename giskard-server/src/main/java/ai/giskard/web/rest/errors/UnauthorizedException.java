
package ai.giskard.web.rest.errors;

import lombok.Getter;

public class UnauthorizedException extends BadRequestAlertException {

    public UnauthorizedException(String actionType, Entity entity) {
        super(String.format("Unauthorized: %s %s not possible  for your role", actionType, entity.getName()), entity.name().toLowerCase(), "accesscontrolerror");
    }
}
