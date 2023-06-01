package ai.giskard.service;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;

@Service

public class SlicingFunctionService extends CallableService<SlicingFunction, SlicingFunctionDTO> {

    private final GiskardMapper giskardMapper;
    private final SlicingFunctionRepository slicingFunctionRepository;

    public SlicingFunctionService(SlicingFunctionRepository slicingFunctionRepository, GiskardMapper giskardMapper) {
        super(slicingFunctionRepository);
        this.giskardMapper = giskardMapper;
        this.slicingFunctionRepository = slicingFunctionRepository;
    }

    @Transactional
    public SlicingFunctionDTO save(SlicingFunctionDTO slicingFunction) {
        return giskardMapper.toDTO(slicingFunctionRepository.save(slicingFunctionRepository.findById(slicingFunction.getUuid())
            .map(existing -> update(existing, slicingFunction))
            .orElseGet(() -> create(slicingFunction))));
    }


    protected SlicingFunction create(SlicingFunctionDTO dto) {
        SlicingFunction function = giskardMapper.fromDTO(dto);
        function.setVersion(slicingFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }


}
