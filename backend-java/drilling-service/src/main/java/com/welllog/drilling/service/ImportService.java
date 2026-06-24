package com.welllog.drilling.service;

import com.welllog.drilling.domain.WellImport;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface ImportService {

    WellImport addImport(Long wellId, MultipartFile file);

    List<WellImport> list(Long wellId);

    WellImport latest(Long wellId);
}
