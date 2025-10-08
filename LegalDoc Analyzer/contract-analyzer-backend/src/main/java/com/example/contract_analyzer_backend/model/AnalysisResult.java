package com.example.contract_analyzer_backend.model;



import java.util.List;

public class AnalysisResult {
    private String contractSummary;
    private List<clause> clauses;
    private List<String> missingClauses;

    // getters and setters
    public String getContractSummary() { return contractSummary; }
    public void setContractSummary(String contractSummary) { this.contractSummary = contractSummary; }

    public List<clause> getClauses() { return clauses; }
    public void setClauses(List<clause> clauses) { this.clauses = clauses; }

    public List<String> getMissingClauses() { return missingClauses; }
    public void setMissingClauses(List<String> missingClauses) { this.missingClauses = missingClauses; }
}

