package ai.giskard.service;

import ai.giskard.domain.ml.*;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.TestTemplatesResponse;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.common.collect.Maps;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.core.io.support.ResourcePatternUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;
import java.util.*;

@Service
@RequiredArgsConstructor
public class CodeTestTemplateService {
    private final Logger log = LoggerFactory.getLogger(CodeTestTemplateService.class);
    public static final String TEMPLATES_LOCATION = "classpath*:aitest/code_test_templates/**yml";
    private final ResourceLoader resourceLoader;
    private final TestSuiteRepository suiteRepository;

    ObjectMapper mapper = new ObjectMapper(new YAMLFactory())
        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

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
            collection.items.forEach(template -> TESTS_BY_ID.put(template.id, template));
            log.debug("Laded {}", resource.getFilename());
        } catch (IOException e) {
            log.error("Failed to read test template: {}", resource.getFilename(), e);
        }
    }

    @Transactional
    public TestTemplatesResponse getTemplates(Long suiteId) {
        TestSuite suite = suiteRepository.getById(suiteId);
        return new TestTemplatesResponse(CODE_TEST_TEMPLATES,
            Maps.transformValues(TESTS_BY_ID, template -> doesTestTemplateSuiteTestSuite(suite, template)));
    }

    public Collection<CodeTestTemplate> getAllTemplates() {
        return TESTS_BY_ID.values();
    }

    @Transactional
    public boolean doesTestTemplateSuiteTestSuite(TestSuite suite, CodeTestTemplate template) {
        ModelType modelType = suite.getModel().getModelType();
        Dataset actualDS = suite.getActualDataset();
        Dataset referenceDS = suite.getReferenceDataset();
        if (template.isMultipleDatasets && (actualDS == null || referenceDS == null)) {
            log.info("Skipping test template '{}' for suite '{}' because not both datasets are specified", template.id, suite.getId());
            return false;
        }
        if (template.isGroundTruthRequired) {
            boolean hasActualTarget = actualDS != null && actualDS.getTarget() != null;
            boolean hasReferenceTarget = referenceDS != null && referenceDS.getTarget() != null;
            if (!hasActualTarget && !hasReferenceTarget) {
                log.info("Skipping test template '{}' for suite '{}' because no ground truth is specified", template.id, suite.getId());
                return false;
            }
        }
        Set<ModelType> templateModelTypes = template.modelTypes;
        if (templateModelTypes != null && !templateModelTypes.contains(modelType)) {
            log.info("Skipping test template '{}' for suite '{}' because it's not suitable for selected model type", template.id, suite.getId());
            return false;
        }
        return true;
    }


}
