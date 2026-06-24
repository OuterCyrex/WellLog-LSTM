package com.welllog.drilling.dto;

import java.time.Instant;

public record WellResponse(
        Long id,
        String name,
        String location,
        String remark,
        Long ownerUserId,
        String ownerUsername,
        Instant createdAt,
        Instant updatedAt,
        long importCount,
        long predictionCount,
        Instant lastImportAt,
        Instant lastPredictionAt
) {
}
