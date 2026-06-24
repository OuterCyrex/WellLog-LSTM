package com.welllog.drilling.repository;

import com.welllog.drilling.domain.Well;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface WellRepository extends JpaRepository<Well, Long> {

    Optional<Well> findByName(String name);

    boolean existsByName(String name);
}
