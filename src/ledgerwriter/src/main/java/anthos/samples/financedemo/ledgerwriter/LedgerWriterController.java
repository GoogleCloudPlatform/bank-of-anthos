package anthos.samples.financedemo.ledgerwriter;

import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.data.redis.connection.stream.Record;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StreamOperations;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;

import javax.annotation.PostConstruct;

@RestController
public class LedgerWriterController {

    ApplicationContext ctx = new AnnotationConfigApplicationContext(LedgerWriterConfig.class);

    private String ledgerStreamKey;

    @PostConstruct
    private void loadEnvironmentVariables() {
        ledgerStreamKey = System.getenv("LEDGER_STREAM");
        if (ledgerStreamKey == null || ledgerStreamKey.isEmpty()) {
            throw new RuntimeException("No stream key provided for Redis backend");
        }
    }

    @PostMapping("/new_transaction")
    public final void addTransaction(@RequestBody Transaction transaction) {
        // TODO: Authenticate the jwt.
        
        // TODO: Extract the account id from the jwt.
        
        // TODO: Perform validation checks
        
        // TODO: Get current balance, check against request

        // Submit Transaction to repository
        RedisTemplate redisTemplate = ctx.getBean(RedisTemplate.class);
        StreamOperations redisStream = redisTemplate.opsForStream();
        redisStream.add(createTransactionRecord(transaction));
    }

    private Record createTransactionRecord(Transaction transaction) {
        return StreamRecords.newRecord()
                .in(ledgerStreamKey)
                .withId(RecordId.autoGenerate())
                .ofObject(transaction);
    }
}
