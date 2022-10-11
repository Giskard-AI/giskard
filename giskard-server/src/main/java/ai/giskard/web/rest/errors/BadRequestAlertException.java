package ai.giskard.web.rest.errors;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;
import org.zalando.problem.AbstractThrowableProblem;
import org.zalando.problem.Status;

public class BadRequestAlertException extends AbstractThrowableProblem {

    private static final long serialVersionUID = 1L;

    private final String entityName;

    private final String errorKey;

    private final String detail;

    public BadRequestAlertException(String defaultMessage, String entityName, String errorKey) {
        this(ErrorConstants.DEFAULT_TYPE, defaultMessage, entityName, errorKey, "");
    }

    public BadRequestAlertException(String defaultMessage) {
        this(ErrorConstants.DEFAULT_TYPE, defaultMessage, null, null, "");
    }

    public BadRequestAlertException(URI type, String defaultMessage, String entityName, String errorKey, String detail) {
        super(type, defaultMessage, Status.BAD_REQUEST, detail, null, null, getAlertParameters(entityName, errorKey, detail));
        this.entityName = entityName;
        this.errorKey = errorKey;
        this.detail = detail;
    }

    public String getEntityName() {
        return entityName;
    }

    public String getErrorKey() {
        return errorKey;
    }

    public String getDetail(){
        return detail;
    }

    private static Map<String, Object> getAlertParameters(String entityName, String errorKey, String detail) {
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("message", "error." + errorKey);
        parameters.put("params", entityName);
        parameters.put("detail", detail);
        return parameters;
    }
}
