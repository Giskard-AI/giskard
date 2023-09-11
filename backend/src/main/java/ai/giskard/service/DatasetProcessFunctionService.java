package ai.giskard.service;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.DatasetProcessFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;

public abstract class DatasetProcessFunctionService<E extends DatasetProcessFunction, D extends DatasetProcessFunctionDTO> extends CallableService<E, D> {

    public DatasetProcessFunctionService(CallableRepository<E> callableRepository, GiskardMapper giskardMapper) {
        super(callableRepository, giskardMapper);
    }

    protected E update(E existingCallable, D dto) {
        existingCallable = super.update(existingCallable, dto);
        existingCallable.setCellLevel(dto.isCellLevel());
        existingCallable.setColumnType(dto.getColumnType());
        existingCallable.setProcessType(dto.getProcessType());
        existingCallable.setClauses(dto.getClauses());
        return existingCallable;
    }
}
