package ai.giskard.service.ee;

public class LicenseExpiredException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public LicenseExpiredException() {
        super("License file is expired.");
    }
}
