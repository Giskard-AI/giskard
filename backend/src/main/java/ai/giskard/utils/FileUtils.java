package ai.giskard.utils;

public class FileUtils {

    private FileUtils() {
        throw new IllegalStateException("Util file");
    }

    public static String getFileName(String name, String extension, boolean sample) {
        StringBuilder builder = new StringBuilder(name);
        if (sample) {
            builder.append(".sample");
        }

        return builder.append(".").append(extension).toString();
    }

}
