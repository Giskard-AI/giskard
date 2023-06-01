package ai.giskard.service.ee;

public class LicenseException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public LicenseException(String message) {
        super(message);
    }
}
