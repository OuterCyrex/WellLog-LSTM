package com.welllog.drilling.repository;

import com.welllog.drilling.domain.WellImport;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface WellImportRepository extends JpaRepository<WellImport, Long> {

    List<WellImport> findByWellIdOrderByIdDesc(Long wellId);

    Optional<WellImport> findTopByWellIdOrderByIdDesc(Long wellId);

    long countByWellId(Long wellId);
}
