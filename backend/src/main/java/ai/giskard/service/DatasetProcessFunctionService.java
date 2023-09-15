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

    protected DatasetProcessFunctionService(CallableRepository<E> callableRepository,
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

    protected E update(E existingCallable, D dto) {
        existingCallable = super.update(existingCallable, dto);
        existingCallable.setCellLevel(dto.isCellLevel());
        existingCallable.setColumnType(dto.getColumnType());
        existingCallable.setProcessType(dto.getProcessType());
        existingCallable.setClauses(dto.getClauses());
        existingCallable.getProjects().addAll(projectRepository.findAllByKeyIn(dto.getProjectKeys()));
        return existingCallable;
    }

}
