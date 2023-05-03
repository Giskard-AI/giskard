package ai.giskard.service;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;

@Service

public class SlicingFunctionService extends CallableService<SlicingFunction, SlicingFunctionDTO> {

    private final GiskardMapper giskardMapper;
    private final SlicingFunctionRepository slicingFunctionRepository;

    public SlicingFunctionService(SlicingFunctionRepository slicingFunctionRepository, GiskardMapper giskardMapper) {
        super(slicingFunctionRepository, giskardMapper);
        this.giskardMapper = giskardMapper;
        this.slicingFunctionRepository = slicingFunctionRepository;
    }

    public SlicingFunctionDTO save(SlicingFunctionDTO slicingFunction) {
        return giskardMapper.toDTO(slicingFunctionRepository.save(slicingFunctionRepository.findById(slicingFunction.getUuid())
            .map(existing -> update(existing, slicingFunction))
            .orElseGet(() -> create(slicingFunction))));
    }


    protected SlicingFunction create(SlicingFunctionDTO dto) {
        SlicingFunction function = giskardMapper.fromDTO(dto);
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setFunction(function));
        }
        function.setVersion(slicingFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }


}
