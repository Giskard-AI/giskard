package ai.giskard.service;

import ai.giskard.domain.SlicingFunction;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.SlicingFunctionRepository;
import ai.giskard.utils.UUID5;
import ai.giskard.web.dto.ComparisonClauseDTO;
import ai.giskard.web.dto.ComparisonType;
import ai.giskard.web.dto.DatasetProcessFunctionType;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static ai.giskard.utils.GiskardStringUtils.escapePythonVariable;
import static ai.giskard.utils.GiskardStringUtils.parsePythonVariable;

@Service

public class SlicingFunctionService extends DatasetProcessFunctionService<SlicingFunction, SlicingFunctionDTO> {

    private final SlicingFunctionRepository slicingFunctionRepository;

    public SlicingFunctionService(SlicingFunctionRepository slicingFunctionRepository,
                                  GiskardMapper giskardMapper,
                                  ProjectRepository projectRepository) {
        super(slicingFunctionRepository, giskardMapper, projectRepository);
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
        function.setProjects(projectRepository.findAllByKeyIn(dto.getProjectKeys()));
        if (function.getArgs() != null) {
            function.getArgs().forEach(arg -> arg.setFunction(function));
        }
        function.setVersion(slicingFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
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

    private Map<String, Object> toCode(ComparisonClauseDTO clause) {
        return Map.of(
            "columnName", clause.getColumnName(),
            "comparisonType", clause.getComparisonType(),
            "value", parsePythonVariable(clause.getValue(), clause.getColumnDtype())
        );
    }

    public SlicingFunctionDTO generate(List<ComparisonClauseDTO> comparisonClauses, String projectKey) throws JsonProcessingException {
        String name = comparisonClauses.stream().map(this::clauseToString).collect(Collectors.joining(" & "));

        SlicingFunction slicingFunction = new SlicingFunction();
        slicingFunction.setUuid(UUID5.nameUUIDFromNamespaceAndString(UUID5.NAMESPACE_OID, name));
        slicingFunction.setArgs(Collections.emptyList());
        slicingFunction.setCode("");
        slicingFunction.setClauses(comparisonClauses.stream().map(this::toCode).collect(Collectors.toList()));
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
        slicingFunction.setProjects(Set.of(projectRepository.getOneByKey(projectKey)));

        return giskardMapper.toDTO(slicingFunctionRepository.save(slicingFunction));
    }

}
