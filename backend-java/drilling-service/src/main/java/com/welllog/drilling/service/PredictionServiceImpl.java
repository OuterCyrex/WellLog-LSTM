package com.welllog.drilling.service;

import com.welllog.drilling.domain.PredictionRecord;
import com.welllog.drilling.domain.WellImport;
import com.welllog.drilling.dto.PythonPredictionResponse;
import com.welllog.drilling.exception.NotFoundException;
import com.welllog.drilling.repository.PredictionRepository;
import com.welllog.drilling.repository.WellImportRepository;
import com.welllog.drilling.repository.WellRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class PredictionServiceImpl implements PredictionService {

    private final WellRepository wellRepository;
    private final WellImportRepository importRepository;
    private final PredictionRepository predictionRepository;
    private final PythonPredictionClient pythonPredictionClient;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public PredictionServiceImpl(WellRepository wellRepository,
                                 WellImportRepository importRepository,
                                 PredictionRepository predictionRepository,
                                 PythonPredictionClient pythonPredictionClient) {
        this.wellRepository = wellRepository;
        this.importRepository = importRepository;
        this.predictionRepository = predictionRepository;
        this.pythonPredictionClient = pythonPredictionClient;
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
        PythonPredictionResponse pythonResult = pythonPredictionClient.predict(source.getFileName(), source.getFileContent());
        record.setModelName(pythonResult.model_name() == null ? "WellLog-LSTM" : pythonResult.model_name());
        record.setStatus("DONE");
        record.setSummary(buildSummary(pythonResult));
        record.setResultJson(toJson(pythonResult));
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

    private String buildSummary(PythonPredictionResponse result) {
        if (result.metrics() == null) {
            return "prediction-complete";
        }
        Object r = result.metrics().get("R");
        Object r2 = result.metrics().get("R2");
        Object mae = result.metrics().get("MAE");
        Object rmse = result.metrics().get("RMSE");
        return "R=%s, R2=%s, MAE=%s, RMSE=%s".formatted(r, r2, mae, rmse);
    }

    private String toJson(PythonPredictionResponse result) {
        try {
            return objectMapper.writeValueAsString(result);
        } catch (JsonProcessingException ex) {
            throw new IllegalArgumentException("Failed to serialize python prediction result");
        }
    }
}
