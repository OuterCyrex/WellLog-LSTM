package com.welllog.drilling.service;

import com.welllog.drilling.domain.PredictionRecord;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface PredictionService {

    PredictionRecord predict(Long wellId, Long importId);

    List<PredictionRecord> list(Long wellId);

    PredictionRecord latest(Long wellId);

    List<PredictionRecord> listAll();

    PredictionRecord getById(Long predictionId);
}
