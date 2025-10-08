package com.example.contract_analyzer_backend.controller;




import com.example.contract_analyzer_backend.model.AnalysisResult;
import com.example.contract_analyzer_backend.service.ContractService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
@CrossOrigin
@RestController
@RequestMapping("/api/contracts")
public class ContractController {

    @Autowired
    private ContractService contractService;

    @PostMapping("/analyze")
    public AnalysisResult analyzeContract(@RequestParam("file") MultipartFile file) throws Exception {
        return contractService.analyzeContract(file);
    }
}

