package ai.giskard.repository;

import ai.giskard.domain.ApiKey;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ApiKeyRepository extends MappableJpaRepository<ApiKey, UUID> {
    List<ApiKey> findAllByUserId(Long userId);
    void deleteApiKeyByIdAndUserId(UUID keyId, Long userId);
}
