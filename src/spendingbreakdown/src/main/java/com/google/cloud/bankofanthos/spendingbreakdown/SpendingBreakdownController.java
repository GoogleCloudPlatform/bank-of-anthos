package com.google.cloud.bankofanthos.spendingbreakdown;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;
import java.util.Collections;

@RestController
public class SpendingBreakdownController {

    @GetMapping("/spending_breakdown")
    public Map<String, Object> getSpendingBreakdown() {
        Map<String, String> spendingData = Collections.singletonMap("january", "no spending");
        return Collections.singletonMap("data", spendingData);
    }
}
