package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.ApiKey;
import ai.giskard.domain.User;
import ai.giskard.repository.ApiKeyRepository;
import ai.giskard.repository.UserRepository;
import jakarta.annotation.PostConstruct;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
    private final Logger log = LoggerFactory.getLogger(ApiKeyService.class);

    private final ApiKeyRepository apiKeyRepository;
    private final ApplicationProperties applicationProperties;
    private final UserRepository userRepository;
    private final Map<String, ApiKey> apiKeysCache = new ConcurrentHashMap<>();

    @PostConstruct
    private void initCache() {
        if (applicationProperties.getDefaultApiKey() != null) {
            // Add a key provided from env to connect external MLWorker in HF
            Optional<User> user = userRepository.findOneByLogin("admin");
            if (user.isPresent() && ApiKey.doesStringLookLikeApiKey(applicationProperties.getDefaultApiKey())) {
                ApiKey key = new ApiKey(user.get());
                key.setKey(applicationProperties.getDefaultApiKey());
                apiKeysCache.put(applicationProperties.getDefaultApiKey(), key);
            } else {
                log.warn("API Key provided but not conforming format.");
            }
        }
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
