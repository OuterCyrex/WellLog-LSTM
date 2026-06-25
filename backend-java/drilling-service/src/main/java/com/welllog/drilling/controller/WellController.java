package com.welllog.drilling.controller;

import com.welllog.drilling.domain.Well;
import com.welllog.drilling.dto.CreateWellRequest;
import com.welllog.drilling.dto.UpdateWellRequest;
import com.welllog.drilling.dto.WellResponse;
import com.welllog.drilling.repository.PredictionRepository;
import com.welllog.drilling.repository.WellImportRepository;
import com.welllog.drilling.service.WellService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/wells")
public class WellController {

    private final WellService wellService;
    private final WellImportRepository importRepository;
    private final PredictionRepository predictionRepository;

    public WellController(WellService wellService,
                          WellImportRepository importRepository,
                          PredictionRepository predictionRepository) {
        this.wellService = wellService;
        this.importRepository = importRepository;
        this.predictionRepository = predictionRepository;
    }

    @GetMapping
    public List<WellResponse> list() {
        return wellService.list().stream().map(this::toResponse).toList();
    }

    @PostMapping
    public WellResponse create(@Valid @RequestBody CreateWellRequest request) {
        return toResponse(wellService.create(request));
    }

    @GetMapping("/{id}")
    public WellResponse get(@PathVariable("id") Long id) {
        return toResponse(wellService.getById(id));
    }

    @PutMapping("/{id}")
    public WellResponse update(@PathVariable("id") Long id, @Valid @RequestBody UpdateWellRequest request) {
        return toResponse(wellService.update(id, request));
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable("id") Long id) {
        wellService.delete(id);
    }

    private WellResponse toResponse(Well well) {
        long importCount = importRepository.countByWellId(well.getId());
        long predictionCount = predictionRepository.countByWellId(well.getId());
        var latestImport = importRepository.findTopByWellIdOrderByIdDesc(well.getId()).orElse(null);
        var latestPrediction = predictionRepository.findTopByWellIdOrderByIdDesc(well.getId()).orElse(null);
        return new WellResponse(
                well.getId(),
                well.getName(),
                well.getLocation(),
                well.getRemark(),
                well.getOwnerUserId(),
                well.getOwnerUsername(),
                well.getCreatedAt(),
                well.getUpdatedAt(),
                importCount,
                predictionCount,
                latestImport == null ? null : latestImport.getCreatedAt(),
                latestPrediction == null ? null : latestPrediction.getCreatedAt()
        );
    }
}
