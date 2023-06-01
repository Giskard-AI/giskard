package ai.giskard.utils;


import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Pattern;

public class GiskardStringUtils {
    private static final Pattern NONLATIN = Pattern.compile("[^\\w-]");
    private static final Pattern WHITESPACE = Pattern.compile("[\\s]");
    private static final Pattern EDGESDHASHES = Pattern.compile("(^-|-$)"); //NOSONAR
    public static final Pattern MULTIDASH = Pattern.compile("-{2,}");

    public static String toSlug(String input) {
        String nowhitespace = WHITESPACE.matcher(input).replaceAll("_");
        String normalized = Normalizer.normalize(nowhitespace, Normalizer.Form.NFD);
        String slug = NONLATIN.matcher(normalized).replaceAll("");
        slug = EDGESDHASHES.matcher(slug).replaceAll("");
        slug = MULTIDASH.matcher(slug).replaceAll("_");
        return slug.toLowerCase(Locale.ENGLISH);
    }

    public static String escapePythonVariable(String value) {
        return escapePythonVariable(value, "str");
    }

    public static String escapePythonVariable(String value, String columnDtype) {
        if (value == null) {
            return "None";
        }

        if (columnDtype.startsWith("int")) {
            return Long.toString(Long.parseLong(value));
        } else if (columnDtype.startsWith("float")) {
            return Double.toString(Double.parseDouble(value));
        } else {
            return String.format("'%s'", value.replace("'", "\\'"));
        }
    }

    public static Object parsePythonVariable(String value, String columnDtype) {
        if (value == null) {
            return null;
        }

        if (columnDtype.startsWith("int")) {
            return Long.parseLong(value);
        } else if (columnDtype.startsWith("float")) {
            return Double.parseDouble(value);
        } else {
            return value;
        }
    }

}
