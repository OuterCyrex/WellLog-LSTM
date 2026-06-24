package com.welllog.drilling.dto;

public record PredictionStats(
        long rows,
        int columns,
        long bytes
) {
}
