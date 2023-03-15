package ai.giskard.utils;

public class LicenseUtils {
    private LicenseUtils() {
        throw new UnsupportedOperationException("Utility class shouldn't be initialized");
    }

    public static boolean isLimitReached(Integer limit, Integer value) {
        if (limit == null)
            return false;
        return value >= limit;
    }
}
