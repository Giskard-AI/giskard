package ai.giskard.repository;

import ai.giskard.domain.SerializedGiskardGeneralSettings;
import org.springframework.stereotype.Repository;

@Repository
public interface GeneralSettingsRepository extends MappableJpaRepository<SerializedGiskardGeneralSettings, Long> {
}
