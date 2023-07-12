package ai.giskard.service;

import ai.giskard.domain.DatasetProcessFunction;
import ai.giskard.repository.ml.CallableRepository;
import ai.giskard.web.dto.DatasetProcessFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;

import java.util.ArrayList;
import java.util.HashSet;

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
        existing.getProjectKeys().addAll(dto.getProjectKeys());
        existing.setProjectKeys(new ArrayList<>(new HashSet<>(existing.getProjectKeys())));
        return existing;
    }
}
