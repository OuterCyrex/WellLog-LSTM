package com.welllog.drilling.service;

import com.welllog.drilling.dto.PythonPredictionResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;

@Component
public class PythonPredictionClient {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String baseUrl;

    public PythonPredictionClient(@Value("${python.predictor.base-url:http://127.0.0.1:8000}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public PythonPredictionResponse predict(String fileName, byte[] fileContent) {
        URI uri = UriComponentsBuilder
                .fromHttpUrl(baseUrl)
                .path("/api/predict")
                .build()
                .toUri();

        ByteArrayResource resource = new ByteArrayResource(fileContent) {
            @Override
            public String getFilename() {
                return fileName == null || fileName.isBlank() ? "upload.csv" : fileName;
            }
        };

        HttpHeaders fileHeaders = new HttpHeaders();
        fileHeaders.setContentType(MediaType.APPLICATION_OCTET_STREAM);
        HttpEntity<ByteArrayResource> filePart = new HttpEntity<>(resource, fileHeaders);

        LinkedMultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", filePart);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<PythonPredictionResponse> response =
                    restTemplate.exchange(uri, HttpMethod.POST, request, PythonPredictionResponse.class);
            return response.getBody();
        } catch (HttpStatusCodeException ex) {
            String message = ex.getResponseBodyAsString();
            throw new IllegalArgumentException(message == null || message.isBlank() ? "Python prediction request failed" : message);
        }
    }
}
