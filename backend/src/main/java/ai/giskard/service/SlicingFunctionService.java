package ai.giskard.service;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.web.dto.ComparisonClauseDTO;
import ai.giskard.web.dto.ComparisonType;
import ai.giskard.web.dto.DatasetProcessFunctionType;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

import static ai.giskard.utils.GiskardStringUtils.escapePythonVariable;

@Service

public class SlicingFunctionService extends DatasetProcessFunctionService<SlicingFunction, SlicingFunctionDTO> {

    private final GiskardMapper giskardMapper;
    private final SlicingFunctionRepository slicingFunctionRepository;

    public SlicingFunctionService(SlicingFunctionRepository slicingFunctionRepository, GiskardMapper giskardMapper) {
        super(slicingFunctionRepository, giskardMapper);
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
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setFunction(function));
        }
        function.setVersion(slicingFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }


    private String clauseCode(ComparisonClauseDTO comparisonClause) {
        ComparisonType comparisonType = comparisonClause.getComparisonType();
        if (comparisonType.isValueRequired()) {
            return String.format(comparisonType.getCodeTemplate(), escapePythonVariable(comparisonClause.getColumnName()),
                escapePythonVariable(comparisonClause.getValue(), comparisonClause.getColumnDtype()));
        } else {
            return String.format(comparisonType.getCodeTemplate(), escapePythonVariable(comparisonClause.getColumnName()));
        }
    }


    private String clauseToString(ComparisonClauseDTO comparisonClause) {
        ComparisonType comparisonType = comparisonClause.getComparisonType();
        if (comparisonType.isValueRequired()) {
            return String.format("%s %s %s", escapePythonVariable(comparisonClause.getColumnName()),
                comparisonType.getSymbol(), escapePythonVariable(comparisonClause.getValue(), comparisonClause.getColumnDtype()));
        } else {
            return String.format("%s %s", escapePythonVariable(comparisonClause.getColumnName()), comparisonType.getSymbol());
        }
    }

    public SlicingFunctionDTO generate(List<ComparisonClauseDTO> comparisonClauses) {
        String name = comparisonClauses.stream().map(this::clauseToString).collect(Collectors.joining(" & "));

        SlicingFunction slicingFunction = new SlicingFunction();
        slicingFunction.setUuid(UUID.randomUUID());
        slicingFunction.setArgs(Collections.emptyList());
        slicingFunction.setCode(String.format("giskard.slicing.slice.Query([%s])", comparisonClauses.stream().map(this::clauseCode).collect(Collectors.joining(", "))));
        slicingFunction.setDisplayName(name);
        slicingFunction.setDoc("Automatically generated slicing function");
        slicingFunction.setModule("");
        slicingFunction.setModuleDoc("");
        slicingFunction.setName(name);
        slicingFunction.setTags(List.of("pickle", "ui"));
        slicingFunction.setVersion(slicingFunctionRepository.countByNameAndModule(slicingFunction.getName(), slicingFunction.getModule()) + 1);
        slicingFunction.setCellLevel(false);
        slicingFunction.setColumnType("");
        slicingFunction.setProcessType(DatasetProcessFunctionType.CLAUSES);

        return giskardMapper.toDTO(slicingFunctionRepository.save(slicingFunction));
    }

}
