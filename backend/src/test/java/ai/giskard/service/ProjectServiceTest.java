package ai.giskard.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

class ProjectServiceTest {

    @Test
    void isProjectKeyValid() {
        assertTrue(ProjectService.isProjectKeyValid("asd"));
        assertTrue(ProjectService.isProjectKeyValid("asd_dsa"));
        assertTrue(ProjectService.isProjectKeyValid("asd_dsa_123"));

        assertFalse(ProjectService.isProjectKeyValid("Asd_dsa_123"));
        assertFalse(ProjectService.isProjectKeyValid("Asd-dsa_123"));
        assertFalse(ProjectService.isProjectKeyValid("Asd-!@#"));
    }
}
