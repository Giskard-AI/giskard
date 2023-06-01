package ai.giskard.service;

import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ml.TestSuiteRepository;
import ai.giskard.web.dto.PrepareDeleteDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UsageService {

    private final TestSuiteRepository testSuiteRepository;
    private final FeedbackRepository feedbackRepository;
    private final GiskardMapper giskardMapper;

    public PrepareDeleteDTO prepareDeleteDataset(String datasetId) {
        PrepareDeleteDTO res = new PrepareDeleteDTO();
        res.setFeedbacks(giskardMapper.toLightFeedbacks(feedbackRepository.findAllByDatasetId(datasetId)));
        res.setSuites(giskardMapper.toLightTestSuites(testSuiteRepository.findByDatasetId(datasetId)));
        return res;
    }

    public PrepareDeleteDTO prepareDeleteModel(String modelId) {
        PrepareDeleteDTO res = new PrepareDeleteDTO();
        res.setFeedbacks(giskardMapper.toLightFeedbacks(feedbackRepository.findAllByModelId(modelId)));
        res.setSuites(giskardMapper.toLightTestSuites(testSuiteRepository.findByModelId(modelId)));
        return res;
    }
}
