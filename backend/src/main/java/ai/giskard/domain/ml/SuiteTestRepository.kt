package ai.giskard.domain.ml;

import org.springframework.data.jpa.repository.JpaRepository

interface SuiteTestRepository : JpaRepository<SuiteTest, Long> {
}
