package ai.giskard.web.rest.controllers;


import ai.giskard.repository.UserRepository;
import ai.giskard.security.GiskardUser;
import ai.giskard.service.ApiKeyService;
import ai.giskard.web.dto.ApiKeyDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v2/apikey")
@RequiredArgsConstructor
public class ApiKeyController {
    private final ApiKeyService apiKeyService;
    private final UserRepository userRepository;
    private final GiskardMapper mapper;

    @PostMapping
    public List<ApiKeyDTO> createApiKey(@AuthenticationPrincipal GiskardUser userDetails) {
        return mapper.apiKeysToApiKeysDTO(apiKeyService.create(userRepository.getOneByLogin(userDetails.getUsername())));
    }

    @GetMapping
    public List<ApiKeyDTO> getApiKeys(@AuthenticationPrincipal GiskardUser userDetails) {
        return mapper.apiKeysToApiKeysDTO(apiKeyService.getKeys(userDetails.getId()));
    }

    @DeleteMapping("/{id}")
    public List<ApiKeyDTO> deleteApiKey(@AuthenticationPrincipal GiskardUser userDetails, @PathVariable UUID id) {
        return mapper.apiKeysToApiKeysDTO(apiKeyService.deleteKey(userDetails.getId(), id));
    }
}
