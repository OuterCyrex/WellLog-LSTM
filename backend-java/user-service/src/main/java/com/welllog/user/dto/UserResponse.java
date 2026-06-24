package com.welllog.user.dto;

import java.time.Instant;

public record UserResponse(
        Long id,
        String username,
        String fullName,
        String email,
        String role,
        boolean enabled,
        Instant createdAt,
        Instant updatedAt
) {
}
