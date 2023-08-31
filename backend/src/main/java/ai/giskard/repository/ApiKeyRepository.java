package ai.giskard.repository;

import ai.giskard.domain.ApiKey;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ApiKeyRepository extends MappableJpaRepository<ApiKey, UUID> {
    void deleteApiKeyByIdAndUserLogin(UUID keyId, String login);
}
