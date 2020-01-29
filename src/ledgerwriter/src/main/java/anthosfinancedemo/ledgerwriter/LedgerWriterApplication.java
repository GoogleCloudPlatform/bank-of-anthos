package anthosfinancedemo.ledgerwriter;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * this class serves as an entry point for the Spring Boot app
 * Here, we check to ensure all required environment variables are set
 */
@SpringBootApplication
public class LedgerWriterApplication {

    public static void main(String[] args) {
        final String[] expectedVars = {"PORT", "LEDGER_ADDR", "LEDGER_STREAM",
            "LEDGER_PORT", "LOCAL_ROUTING_NUM", "BALANCES_API_ADDR", "PUB_KEY_PATH"};
        for (String v : expectedVars) {
            String value = System.getenv(v);
            if (value == null) {
                System.out.format("error: %s environment variable not set", v);
                System.exit(1);
            }
        }
        SpringApplication.run(LedgerWriterApplication.class, args);
    }
}
