package com.example.contract_analyzer_backend.model;

import java.util.List;
import java.util.Map;

public class clause {
    private String type;
    private String text;
    private Map<String, Object> facts;
    private String explanationSimple;
    private List<String> keyFacts;
    private List<String> riskFlags;

    // getters and setters
    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public Map<String, Object> getFacts() { return facts; }
    public void setFacts(Map<String, Object> facts) { this.facts = facts; }

    public String getExplanationSimple() { return explanationSimple; }
    public void setExplanationSimple(String explanationSimple) { this.explanationSimple = explanationSimple; }

    public List<String> getKeyFacts() { return keyFacts; }
    public void setKeyFacts(List<String> keyFacts) { this.keyFacts = keyFacts; }

    public List<String> getRiskFlags() { return riskFlags; }
    public void setRiskFlags(List<String> riskFlags) { this.riskFlags = riskFlags; }
}
