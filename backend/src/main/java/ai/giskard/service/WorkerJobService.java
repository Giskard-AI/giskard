package ai.giskard.service;

import ai.giskard.repository.WorkerJobRepository;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.WorkerJobDTO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
@RequiredArgsConstructor
public class WorkerJobService {

    /**
     * List of all @{@link WorkerJobRepository} injected automatically
     */
    private final List<WorkerJobRepository<?>> workerJobRepositories;
    private final GiskardMapper giskardMapper;

    public List<WorkerJobDTO> getRunningWorkerJobs() {
        return giskardMapper.workerJobsToDTOs(workerJobRepositories.stream()
            .flatMap(workerJobRepository -> workerJobRepository.findRunningJobs().stream())
            .toList());
    }
}
