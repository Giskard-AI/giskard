package ai.giskard.service;

import ai.giskard.domain.ApiKey;
import ai.giskard.domain.User;
import ai.giskard.repository.ApiKeyRepository;
import jakarta.annotation.PostConstruct;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class ApiKeyService {
    private final ApiKeyRepository apiKeyRepository;
    private final Map<String, ApiKey> apiKeysCache = new ConcurrentHashMap<>();

    @PostConstruct
    private void initCache() {
        apiKeyRepository.findAll().forEach(apiKey -> apiKeysCache.put(apiKey.getKey(), apiKey));
    }

    public List<ApiKey> create(User user) {
        ApiKey key = apiKeyRepository.save(new ApiKey(user));
        apiKeysCache.put(key.getKey(), key);
        return getKeys(user.getId());
    }

    public Optional<ApiKey> getKey(@NotNull String key) {
        return Optional.ofNullable(apiKeysCache.get(key));
    }

    public List<ApiKey> getKeys(Long userId) {
        return apiKeysCache.values().stream().filter(k -> k.getUser().getId().equals(userId)).toList();
    }

    @Transactional
    public List<ApiKey> deleteKey(Long userId, UUID key) {
        apiKeyRepository.deleteApiKeyByIdAndUserId(key, userId);
        apiKeysCache.values().stream()
            .filter(k -> k.getId().equals(key)).findFirst()
            .ifPresent(k -> apiKeysCache.remove(k.getKey()));
        return getKeys(userId);
    }
}
