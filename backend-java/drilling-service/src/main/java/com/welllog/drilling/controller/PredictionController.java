package com.welllog.drilling.controller;

import com.welllog.drilling.domain.PredictionRecord;
import com.welllog.drilling.dto.PredictionResponse;
import com.welllog.drilling.service.PredictionService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping
public class PredictionController {

    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @GetMapping("/api/wells/{wellId}/predictions")
    public List<PredictionResponse> listByWell(@PathVariable Long wellId) {
        return predictionService.list(wellId).stream().map(this::toResponse).toList();
    }

    @PostMapping("/api/wells/{wellId}/predict")
    public PredictionResponse predict(@PathVariable Long wellId, @RequestParam(required = false) Long importId) {
        return toResponse(predictionService.predict(wellId, importId));
    }

    @GetMapping("/api/predictions")
    public List<PredictionResponse> listAll() {
        return predictionService.listAll().stream().map(this::toResponse).toList();
    }

    @GetMapping("/api/predictions/{predictionId}")
    public PredictionResponse getById(@PathVariable Long predictionId) {
        return toResponse(predictionService.getById(predictionId));
    }

    private PredictionResponse toResponse(PredictionRecord item) {
        String wellName = "";
        return new PredictionResponse(
                item.getId(),
                item.getWellId(),
                item.getImportId(),
                item.getModelName(),
                item.getStatus(),
                item.getSummary(),
                item.getResultJson(),
                item.getCreatedAt(),
                item.getUpdatedAt(),
                wellName
        );
    }
}
