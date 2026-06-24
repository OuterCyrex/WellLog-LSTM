package com.welllog.drilling.service;

import com.welllog.drilling.domain.Well;
import com.welllog.drilling.dto.CreateWellRequest;
import com.welllog.drilling.dto.UpdateWellRequest;

import java.util.List;

public interface WellService {

    Well create(CreateWellRequest request);

    Well getById(Long id);

    List<Well> list();

    Well update(Long id, UpdateWellRequest request);

    void delete(Long id);
}
