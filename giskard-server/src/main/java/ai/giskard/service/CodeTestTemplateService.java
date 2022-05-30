package ai.giskard.service;

import ai.giskard.domain.ml.CodeTestCollection;
import ai.giskard.domain.ml.CodeTestTemplate;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.core.io.support.ResourcePatternUtils;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;
import java.util.*;

@Service
@RequiredArgsConstructor
public class CodeTestTemplateService {
    public static final String TEMPLATES_LOCATION = "classpath*:aitest/code_test_templates/**yml";
    private final ResourceLoader resourceLoader;
    private final Logger log = LoggerFactory.getLogger(CodeTestTemplateService.class);
    ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

    private static final List<CodeTestCollection> CODE_TEST_TEMPLATES = new ArrayList<>();
    private static final Map<String, CodeTestTemplate> TESTS_BY_ID = new HashMap<>();

    @PostConstruct
    public void init() {
        readTemplates();
    }

    private void readTemplates() {
        try {
            for (Resource resource : ResourcePatternUtils.getResourcePatternResolver(resourceLoader).getResources(TEMPLATES_LOCATION)) {
                readTestResource(resource);
            }
        } catch (IOException e) {
            log.error("Failed to read code based test templates", e);
        }
    }

    private void readTestResource(Resource resource) {
        try {
            InputStream inputStream = resource.getInputStream();
            CodeTestCollection collection = mapper.readValue(inputStream, CodeTestCollection.class);
            CODE_TEST_TEMPLATES.add(collection);
            collection.items.forEach(test -> TESTS_BY_ID.put(test.getId(), test));
            log.debug("Laded {}", resource.getFilename());
        } catch (IOException e) {
            log.error("Failed to read test template: {}", resource.getFilename(), e);
        }
    }


    public List<CodeTestCollection> getTemplates() {
        return CODE_TEST_TEMPLATES;
    }

    public Collection<CodeTestTemplate> getAllTemplates() {
        return TESTS_BY_ID.values();
    }

}
