package ai.giskard.service;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.DatasetProcessFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;

public abstract class DatasetProcessFunctionService<E extends DatasetProcessFunction, D extends DatasetProcessFunctionDTO> extends CallableService<E, D> {

    public DatasetProcessFunctionService(CallableRepository<E> callableRepository, GiskardMapper giskardMapper) {
        super(callableRepository, giskardMapper);
    }

    protected E update(E existing, D dto) {
        existing = super.update(existing, dto);
        existing.setCellLevel(dto.isCellLevel());
        existing.setColumnType(dto.getColumnType());
        existing.setProcessType(dto.getProcessType());
        existing.setClauses(dto.getClauses());
        // TODO: allow list of project to not override the project key
        existing.setProjectKey(dto.getProjectKey());
        return existing;
    }
}
