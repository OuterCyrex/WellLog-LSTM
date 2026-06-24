package com.welllog.drilling.dto;

import java.time.Instant;

public record PredictionResponse(
        Long id,
        Long wellId,
        Long importId,
        String modelName,
        String status,
        String summary,
        String resultJson,
        Instant createdAt,
        Instant updatedAt,
        String wellName
) {
}
