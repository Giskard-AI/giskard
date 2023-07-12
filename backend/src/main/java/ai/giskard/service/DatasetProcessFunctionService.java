package ai.giskard.service;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.DatasetProcessFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.hibernate.Hibernate;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

public abstract class DatasetProcessFunctionService<E extends DatasetProcessFunction, D extends DatasetProcessFunctionDTO> extends CallableService<E, D> {

    protected ProjectRepository projectRepository;

    public DatasetProcessFunctionService(CallableRepository<E> callableRepository,
                                         GiskardMapper giskardMapper,
                                         ProjectRepository projectRepository) {
        super(callableRepository, giskardMapper);
        this.projectRepository = projectRepository;
    }

    @Transactional(readOnly = true)
    @Override
    public E getInitialized(UUID uuid) {
        E callable = super.getInitialized(uuid);
        Hibernate.initialize(callable.getProjects());
        return callable;
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
