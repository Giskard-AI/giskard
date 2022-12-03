package ai.giskard.service;

import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.PrepareDeleteDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UsageService {

    private final TestSuiteRepository testSuiteRepository;
    private final FeedbackRepository feedbackRepository;

    public PrepareDeleteDTO prepareDeleteDataset(Long datasetId) {
        PrepareDeleteDTO res = new PrepareDeleteDTO();
        res.setFeedbackCount(feedbackRepository.findAllByDatasetId(datasetId).size());
        res.setSuiteCount(testSuiteRepository.findByDatasetId(datasetId).size());
        return res;
    }

    public PrepareDeleteDTO prepareDeleteModel(Long modelId) {
        PrepareDeleteDTO res = new PrepareDeleteDTO();
        res.setFeedbackCount(feedbackRepository.findAllByModelId(modelId).size());
        res.setSuiteCount(testSuiteRepository.findByModelId(modelId).size());
        return res;
    }
}
