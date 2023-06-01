package ai.giskard.service;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;

@Service

public class TransformationFunctionService extends CallableService<TransformationFunction, TransformationFunctionDTO> {

    private final GiskardMapper giskardMapper;
    private final TransformationFunctionRepository transformationFunctionRepository;

    public TransformationFunctionService(TransformationFunctionRepository transformationFunctionRepository, GiskardMapper giskardMapper) {
        super(transformationFunctionRepository, giskardMapper);
        this.giskardMapper = giskardMapper;
        this.transformationFunctionRepository = transformationFunctionRepository;
    }

    @Transactional
    public TransformationFunctionDTO save(TransformationFunctionDTO transformationFunction) {
        return giskardMapper.toDTO(transformationFunctionRepository.save(transformationFunctionRepository.findById(transformationFunction.getUuid())
            .map(existing -> update(existing, transformationFunction))
            .orElseGet(() -> create(transformationFunction))));
    }


    protected TransformationFunction create(TransformationFunctionDTO dto) {
        TransformationFunction function = giskardMapper.fromDTO(dto);
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setFunction(function));
        }
        function.setVersion(transformationFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }


}
