package com.welllog.drilling.controller;

import com.welllog.drilling.domain.WellImport;
import com.welllog.drilling.dto.ImportResponse;
import com.welllog.drilling.service.ImportService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/wells/{wellId}/imports")
public class ImportController {

    private final ImportService importService;

    public ImportController(ImportService importService) {
        this.importService = importService;
    }

    @GetMapping
    public List<ImportResponse> list(@PathVariable Long wellId) {
        return importService.list(wellId).stream().map(this::toResponse).toList();
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ImportResponse upload(@PathVariable Long wellId, @RequestPart("file") MultipartFile file) {
        return toResponse(importService.addImport(wellId, file));
    }

    private ImportResponse toResponse(WellImport item) {
        return new ImportResponse(
                item.getId(),
                item.getWellId(),
                item.getFileName(),
                item.getContentType(),
                item.getFileSize(),
                item.getCreatedAt(),
                item.getUpdatedAt()
        );
    }
}
