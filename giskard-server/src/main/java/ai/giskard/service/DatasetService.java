package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.security.SecurityUtils;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.web.dto.ml.DatasetDetailsDTO;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.EntityNotFoundException;
import ai.giskard.web.rest.errors.NotInDatabaseException;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.Table;

import javax.validation.constraints.NotNull;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Objects;
import java.util.Set;

@Service
@Transactional
@RequiredArgsConstructor
public class DatasetService {

    final UserRepository userRepository;
    final DatasetRepository datasetRepository;
    private final ApplicationProperties applicationProperties;

    public Table getTableFromDatasetId(@NotNull Long id) {
        Dataset dataset = datasetRepository.findById(id).orElseThrow(() -> new EntityNotFoundException(Entity.DATASET, id));
        Path filePath = Paths.get(applicationProperties.getBucketPath(), dataset.getLocation());
        String filePathName = filePath.toAbsolutePath().toString().replace(".zst", "");
        return Table.read().csv(filePathName);
    }

    /**
     * Get details of dataset
     *
     * @param id dataset's id
     * @return details dto of the dataset
     */
    public DatasetDetailsDTO getDetails(@NotNull Long id) {
        Table table = getTableFromDatasetId(id);
        DatasetDetailsDTO details = new DatasetDetailsDTO();
        details.setNumberOfRows(table.rowCount());
        return details;
    }

    /**
     * Get filtered rows
     *
     * @param id       dataset id
     * @param rangeMin min range of the dataset
     * @param rangeMax max range of the dataset
     * @return filtered table
     */
    public Table getRows(@NotNull Long id, @NotNull int rangeMin, @NotNull int rangeMax) {
        Table table = getTableFromDatasetId(id);
        table.addColumns(IntColumn.indexColumn("Index", table.rowCount(), 0));
        Table filteredTable = table.inRange(rangeMin, rangeMax);
        return filteredTable;
    }
}
