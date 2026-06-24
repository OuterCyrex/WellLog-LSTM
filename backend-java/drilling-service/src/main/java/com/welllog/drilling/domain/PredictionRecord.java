package com.welllog.drilling.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;

@Entity
@Table(name = "predictions")
public class PredictionRecord extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long wellId;

    @Column
    private Long importId;

    @Column(nullable = false, length = 60)
    private String modelName;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(length = 500)
    private String summary;

    @Lob
    @Column(nullable = false)
    private String resultJson;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getWellId() {
        return wellId;
    }

    public void setWellId(Long wellId) {
        this.wellId = wellId;
    }

    public Long getImportId() {
        return importId;
    }

    public void setImportId(Long importId) {
        this.importId = importId;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public String getResultJson() {
        return resultJson;
    }

    public void setResultJson(String resultJson) {
        this.resultJson = resultJson;
    }
}
