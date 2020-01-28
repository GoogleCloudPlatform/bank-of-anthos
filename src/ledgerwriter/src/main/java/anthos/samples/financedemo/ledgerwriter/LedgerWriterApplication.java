package anthos.samples.financedemo.ledgerwriter;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

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
