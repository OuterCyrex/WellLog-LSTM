package com.welllog.drilling.dto;

public record UserSummary(
        Long id,
        String username,
        String fullName,
        String email,
        String role,
        boolean enabled
) {
}
