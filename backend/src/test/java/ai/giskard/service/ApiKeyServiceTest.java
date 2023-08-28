package ai.giskard.service;

import ai.giskard.domain.ApiKey;
import ai.giskard.domain.User;
import ai.giskard.repository.ApiKeyRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.Collections;
import java.util.List;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ApiKeyServiceTest {
    private ApiKeyService service;

    @BeforeEach
    public void setup() {
        ApiKeyRepository repo = mock(ApiKeyRepository.class);
        ApiKey key = new ApiKey(new User());
        when(repo.save(Mockito.any())).thenReturn(key);
        service = new ApiKeyService(repo);
    }

    @Test
    void save() {
        User userA = new User();
        userA.setLogin("userA");
        userA.setId(1L);

        List<ApiKey> apiKeys = service.create(userA);
        System.out.println(123);
        // System.out.println(repo);
    }
}
