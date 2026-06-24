package com.welllog.drilling.dto;

import java.time.Instant;

public record ImportResponse(
        Long id,
        Long wellId,
        String fileName,
        String contentType,
        long fileSize,
        Instant createdAt,
        Instant updatedAt
) {
}
