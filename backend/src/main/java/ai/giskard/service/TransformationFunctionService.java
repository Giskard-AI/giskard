package ai.giskard.service;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.apache.logging.log4j.util.Strings;
import org.springframework.stereotype.Service;

@Service

public class TransformationFunctionService extends DatasetProcessFunctionService<TransformationFunction, TransformationFunctionDTO> {

    private final TransformationFunctionRepository transformationFunctionRepository;

    public TransformationFunctionService(TransformationFunctionRepository transformationFunctionRepository, GiskardMapper giskardMapper) {
        super(transformationFunctionRepository, giskardMapper);
        this.transformationFunctionRepository = transformationFunctionRepository;
    }

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

        if (Strings.isBlank(function.getDisplayName())) {
            function.setDisplayName(function.getModule() + "." + function.getName());
        }

        function.setVersion(transformationFunctionRepository.countByDisplayName(function.getDisplayName()) + 1);

        return function;
    }


}
