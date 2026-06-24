package com.welllog.drilling.dto;

public record UpdateWellRequest(
        String name,
        String location,
        String remark,
        Long ownerUserId
) {
}
