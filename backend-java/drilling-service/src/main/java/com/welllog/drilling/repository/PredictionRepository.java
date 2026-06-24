package com.welllog.drilling.repository;

import com.welllog.drilling.domain.PredictionRecord;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PredictionRepository extends JpaRepository<PredictionRecord, Long> {

    List<PredictionRecord> findByWellIdOrderByIdDesc(Long wellId);

    Optional<PredictionRecord> findTopByWellIdOrderByIdDesc(Long wellId);

    long countByWellId(Long wellId);
}
