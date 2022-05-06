package ai.giskard.service;

import ai.giskard.domain.ml.CodeTestCollection;
import ai.giskard.domain.ml.CodeTestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.ResourceUtils;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.PathMatcher;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

@Service
public class CodeTestTemplateService {
    public static final String TEMPLATES_DIR = "classpath:aitest/code_test_templates";
    public static final String TEMPLATE_SEARCH_PATTERN = "glob:**.yml";
    private final Logger log = LoggerFactory.getLogger(CodeTestTemplateService.class);
    ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

    private List<CodeTestCollection> CODE_TEST_TEMPLATES;
    private Map<String, CodeTestTemplate> TESTS_BY_ID;

    @PostConstruct
    public void init() {
        readTemplates();
    }

    private void readTemplates() {
        CODE_TEST_TEMPLATES = new ArrayList<>();
        TESTS_BY_ID = new HashMap<>();
        PathMatcher matcher = FileSystems.getDefault().getPathMatcher(TEMPLATE_SEARCH_PATTERN);

        try (Stream<Path> walk = Files.walk(ResourceUtils.getFile(TEMPLATES_DIR).toPath())) {
            walk.filter(matcher::matches).forEach(path -> {
                try {
                    CodeTestCollection collection = mapper.readValue(path.toFile(), CodeTestCollection.class);
                    CODE_TEST_TEMPLATES.add(collection);
                    collection.items.forEach(test->{
                        TESTS_BY_ID.put(test.getId(), test);
                    });
                } catch (IOException e) {
                    log.error("Failed to read test template: {}", path, e);
                }
            });
        } catch (IOException e) {
            log.error("Failed to read code based test templates", e);
        }
    }


    public List<CodeTestCollection> getTemplates() {
        return CODE_TEST_TEMPLATES;
    }
}
