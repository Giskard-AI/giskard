package ai.giskard.service;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.DatasetProcessFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;

public abstract class DatasetProcessFunctionService<E extends DatasetProcessFunction, D extends DatasetProcessFunctionDTO> extends CallableService<E, D> {

    protected ProjectRepository projectRepository;

    public DatasetProcessFunctionService(CallableRepository<E> callableRepository,
                                         GiskardMapper giskardMapper,
                                         ProjectRepository projectRepository) {
        super(callableRepository, giskardMapper);
        this.projectRepository = projectRepository;
    }

    protected E update(E existing, D dto) {
        existing = super.update(existing, dto);
        existing.setCellLevel(dto.isCellLevel());
        existing.setColumnType(dto.getColumnType());
        existing.setProcessType(dto.getProcessType());
        existing.setClauses(dto.getClauses());
        existing.getProjects().addAll(projectRepository.findAllByKeyIn(dto.getProjectKeys()));
        return existing;
    }
}
