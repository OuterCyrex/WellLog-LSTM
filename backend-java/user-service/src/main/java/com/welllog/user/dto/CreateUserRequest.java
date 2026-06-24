package com.welllog.user.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record CreateUserRequest(
        @NotBlank String username,
        @NotBlank String password,
        String fullName,
        @Email String email,
        String role
) {
}
