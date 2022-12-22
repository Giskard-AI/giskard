package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Slice;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ml.SliceRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.SliceDTO;
import ai.giskard.web.dto.ml.TestSuiteDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Service
@Transactional
@RequiredArgsConstructor
public class SliceService {
    private final GiskardMapper giskardMapper;
    private final SliceRepository sliceRepository;
    private final MLWorkerService mlWorkerService;

    public SliceDTO createSlice(Slice slice) {
        Slice sl = sliceRepository.save(slice);
        return giskardMapper.sliceToSliceDTO(sl);
    }

    public List<Integer> getSlicedRowsForDataset(Long sliceId, Dataset dataset) throws IOException {
        Slice slice = sliceRepository.getById(sliceId);

        try (MLWorkerClient client = mlWorkerService.createClient(true)) {
            return mlWorkerService.filterDataset(client, dataset, slice.getCode());
        } catch (Exception e) {
            return null; // todo exception?
        }
    }
}
