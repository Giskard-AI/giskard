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
        String nowhitespace = WHITESPACE.matcher(input).replaceAll("-");
        String normalized = Normalizer.normalize(nowhitespace, Normalizer.Form.NFD);
        String slug = NONLATIN.matcher(normalized).replaceAll("");
        slug = EDGESDHASHES.matcher(slug).replaceAll("");
        slug = MULTIDASH.matcher(slug).replaceAll("-");
        return slug.toLowerCase(Locale.ENGLISH);
    }
}
