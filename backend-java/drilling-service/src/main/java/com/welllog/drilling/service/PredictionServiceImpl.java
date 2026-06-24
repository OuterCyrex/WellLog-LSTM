package com.welllog.drilling.service;

import com.welllog.drilling.domain.PredictionRecord;
import com.welllog.drilling.domain.WellImport;
import com.welllog.drilling.exception.NotFoundException;
import com.welllog.drilling.repository.PredictionRepository;
import com.welllog.drilling.repository.WellImportRepository;
import com.welllog.drilling.repository.WellRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

@Service
@Transactional
public class PredictionServiceImpl implements PredictionService {

    private final WellRepository wellRepository;
    private final WellImportRepository importRepository;
    private final PredictionRepository predictionRepository;

    public PredictionServiceImpl(WellRepository wellRepository,
                                 WellImportRepository importRepository,
                                 PredictionRepository predictionRepository) {
        this.wellRepository = wellRepository;
        this.importRepository = importRepository;
        this.predictionRepository = predictionRepository;
    }

    @Override
    public PredictionRecord predict(Long wellId, Long importId) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        WellImport source = resolveImport(wellId, importId);
        PredictionRecord record = new PredictionRecord();
        record.setWellId(wellId);
        record.setImportId(source.getId());
        record.setModelName("stub-lstm-v1");
        record.setStatus("DONE");

        PredictionStats stats = analyze(source.getFileContent());
        record.setSummary("rows=" + stats.rows() + ", columns=" + stats.columns());
        record.setResultJson(toJson(source, stats));
        return predictionRepository.save(record);
    }

    @Override
    @Transactional(readOnly = true)
    public List<PredictionRecord> list(Long wellId) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        return predictionRepository.findByWellIdOrderByIdDesc(wellId);
    }

    @Override
    @Transactional(readOnly = true)
    public PredictionRecord latest(Long wellId) {
        if (!wellRepository.existsById(wellId)) {
            throw new NotFoundException("Well not found");
        }
        return predictionRepository.findTopByWellIdOrderByIdDesc(wellId)
                .orElseThrow(() -> new NotFoundException("Prediction not found"));
    }

    @Override
    @Transactional(readOnly = true)
    public List<PredictionRecord> listAll() {
        return predictionRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public PredictionRecord getById(Long predictionId) {
        return predictionRepository.findById(predictionId)
                .orElseThrow(() -> new NotFoundException("Prediction not found"));
    }

    private WellImport resolveImport(Long wellId, Long importId) {
        if (importId != null) {
            return importRepository.findById(importId)
                    .filter(item -> item.getWellId().equals(wellId))
                    .orElseThrow(() -> new NotFoundException("Import not found"));
        }
        return importRepository.findTopByWellIdOrderByIdDesc(wellId)
                .orElseThrow(() -> new NotFoundException("Import not found"));
    }

    private PredictionStats analyze(byte[] fileContent) {
        String text = new String(fileContent, StandardCharsets.UTF_8);
        String[] lines = text.split("\\R");
        long rows = Arrays.stream(lines).filter(line -> !line.isBlank()).count();
        int columns = 0;
        for (String line : lines) {
            if (!line.isBlank()) {
                columns = Math.max(columns, splitColumns(line));
            }
        }
        return new PredictionStats(rows, columns, fileContent.length);
    }

    private int splitColumns(String line) {
        String[] comma = line.split(",");
        if (comma.length > 1) {
            return comma.length;
        }
        String[] tabs = line.split("\\t");
        if (tabs.length > 1) {
            return tabs.length;
        }
        return line.trim().isEmpty() ? 0 : 1;
    }

    private String toJson(WellImport source, PredictionStats stats) {
        return """
                {
                  "status": "DONE",
                  "modelName": "stub-lstm-v1",
                  "importId": %d,
                  "fileName": "%s",
                  "rows": %d,
                  "columns": %d,
                  "bytes": %d
                }
                """.formatted(
                source.getId(),
                escape(source.getFileName()),
                stats.rows(),
                stats.columns(),
                stats.bytes()
        );
    }

    private String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
