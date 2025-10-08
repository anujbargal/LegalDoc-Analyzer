package com.example.contract_analyzer_backend.service;

import com.example.contract_analyzer_backend.model.AnalysisResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@Service
public class ContractService {

    @Value("${fastapi.url:http://localhost:8000}")
    private String fastApiUrl;

    public AnalysisResult analyzeContract(MultipartFile file) throws IOException {
        RestTemplate restTemplate = new RestTemplate();

        // Wrap MultipartFile in InputStreamResource
        InputStreamResource resource = new InputStreamResource(file.getInputStream()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }

            @Override
            public long contentLength() throws IOException {
                return file.getSize();
            }
        };

        // Prepare multipart/form-data body
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);

        // Set headers
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        headers.setAccept(MediaType.parseMediaTypes("application/json")); // Expect JSON response

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        // Send POST request
        ResponseEntity<AnalysisResult> response = restTemplate.postForEntity(
                fastApiUrl + "/analyze",
                requestEntity,
                AnalysisResult.class
        );

        return response.getBody();
    }
}
