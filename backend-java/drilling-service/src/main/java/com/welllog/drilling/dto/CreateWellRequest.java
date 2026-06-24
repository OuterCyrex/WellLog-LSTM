package com.welllog.drilling.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreateWellRequest(
        @NotBlank String name,
        String location,
        String remark,
        @NotNull Long ownerUserId
) {
}
