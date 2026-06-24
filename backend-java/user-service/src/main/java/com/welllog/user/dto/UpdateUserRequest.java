package com.welllog.user.dto;

import jakarta.validation.constraints.Email;

public record UpdateUserRequest(
        String password,
        String fullName,
        @Email String email,
        String role,
        Boolean enabled
) {
}
