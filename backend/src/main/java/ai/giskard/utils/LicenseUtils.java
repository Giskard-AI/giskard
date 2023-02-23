package ai.giskard.utils;

public class LicenseUtils {

    public static boolean isLimitReached(Integer limit, Integer value) {
        if (limit == null)
            return false;
        return value >= limit;
    }
}
