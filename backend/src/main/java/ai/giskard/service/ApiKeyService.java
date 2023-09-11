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
        return getKeys(user.getLogin());
    }

    public Optional<ApiKey> getKey(@NotNull String key) {
        return Optional.ofNullable(apiKeysCache.get(key));
    }

    public List<ApiKey> getKeys(String username) {
        return apiKeysCache.values().stream().filter(k -> k.getUser().getLogin().equals(username)).toList();
    }

    @Transactional
    public List<ApiKey> deleteKey(String username, UUID key) {
        apiKeyRepository.deleteApiKeyByIdAndUserLogin(key, username);
        apiKeysCache.values().stream()
            .filter(k -> k.getId().equals(key)).findFirst()
            .ifPresent(k -> apiKeysCache.remove(k.getKey()));
        return getKeys(username);
    }
}
