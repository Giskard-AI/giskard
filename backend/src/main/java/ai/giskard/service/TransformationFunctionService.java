package ai.giskard.service;

import ai.giskard.domain.TransformationFunction;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TransformationFunctionRepository;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;

@Service

public class TransformationFunctionService extends DatasetProcessFunctionService<TransformationFunction, TransformationFunctionDTO> {

    private final TransformationFunctionRepository transformationFunctionRepository;

    public TransformationFunctionService(TransformationFunctionRepository transformationFunctionRepository,
                                         GiskardMapper giskardMapper,
                                         ProjectRepository projectRepository) {
        super(transformationFunctionRepository, giskardMapper, projectRepository);
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
        function.setVersion(transformationFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }


}
