package com.welllog.drilling.service;

import com.welllog.drilling.domain.WellImport;
import com.welllog.drilling.exception.NotFoundException;
import com.welllog.drilling.repository.WellImportRepository;
import com.welllog.drilling.repository.WellRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@Service
@Transactional
public class ImportServiceImpl implements ImportService {

    private final WellRepository wellRepository;
    private final WellImportRepository importRepository;

    public ImportServiceImpl(WellRepository wellRepository, WellImportRepository importRepository) {
        this.wellRepository = wellRepository;
        this.importRepository = importRepository;
    }

    @Override
    public WellImport addImport(Long wellId, MultipartFile file) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("File is required");
        }
        try {
            WellImport record = new WellImport();
            record.setWellId(wellId);
            record.setFileName(file.getOriginalFilename() == null ? "upload.dat" : file.getOriginalFilename());
            record.setContentType(file.getContentType());
            record.setFileSize(file.getSize());
            record.setFileContent(file.getBytes());
            return importRepository.save(record);
        } catch (IOException ex) {
            throw new IllegalArgumentException("Failed to read uploaded file");
        }
    }

    @Override
    @Transactional(readOnly = true)
    public List<WellImport> list(Long wellId) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        return importRepository.findByWellIdOrderByIdDesc(wellId);
    }

    @Override
    @Transactional(readOnly = true)
    public WellImport latest(Long wellId) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        return importRepository.findTopByWellIdOrderByIdDesc(wellId)
                .orElseThrow(() -> new NotFoundException("Import not found"));
    }
}
