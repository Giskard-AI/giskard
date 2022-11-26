package ai.giskard.repository;

import ai.giskard.domain.SerializedGiskardGeneralSettings;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface GeneralSettingsRepository extends JpaRepository<SerializedGiskardGeneralSettings, Long> {}
