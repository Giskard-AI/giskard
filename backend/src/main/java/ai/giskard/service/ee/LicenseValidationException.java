package ai.giskard.service.ee;

public class LicenseValidationException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public LicenseValidationException() {
        super("License file is invalid.");
    }
}
