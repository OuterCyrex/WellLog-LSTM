package com.welllog.drilling.dto;

import java.util.List;
import java.util.Map;

public record PythonPredictionResponse(
        String well_name,
        String model_name,
        Map<String, Object> metrics,
        List<Object> depth,
        List<Object> y_true,
        List<Object> y_pred
) {
}
