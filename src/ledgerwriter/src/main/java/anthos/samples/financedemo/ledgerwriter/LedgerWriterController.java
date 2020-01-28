package anthos.samples.financedemo.ledgerwriter;

import io.lettuce.core.api.StatefulRedisConnection;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
public class LedgerWriterController {

    ApplicationContext ctx = new AnnotationConfigApplicationContext(LedgerWriterConfig.class);

    private final String ledgerStreamKey;

    public LedgerWriterController() {
        ledgerStreamKey = System.getenv("LEDGER_STREAM");
        if (ledgerStreamKey == null || ledgerStreamKey.isEmpty()) {
            throw new RuntimeException("No stream key provided for Redis backend");
        }
    }

    @GetMapping("/ready")
    public ResponseEntity<String> readiness() {
        return ResponseEntity.ok("Server ready");
    }

    @PostMapping(value = "/new_transaction", consumes = "application/json")
    public ResponseEntity<String> addTransaction(@RequestBody Transaction transaction) {
        // TODO: Authenticate the jwt.
        
        // TODO: Extract the account id from the jwt.
        
        // TODO: Perform validation checks
        
        // TODO: Get current balance, check against request

        // Submit Transaction to repository
        submitTransaction(transaction);

        return ResponseEntity.accepted().body("Transaction submitted");
    }

    private void submitTransaction(Transaction transaction) {
        StatefulRedisConnection redisConnection = ctx.getBean(StatefulRedisConnection.class);
        redisConnection.async().xadd(ledgerStreamKey, transaction);
    }
}
