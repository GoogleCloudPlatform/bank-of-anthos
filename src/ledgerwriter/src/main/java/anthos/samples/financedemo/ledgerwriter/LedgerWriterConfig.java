package anthos.samples.financedemo.ledgerwriter;

import io.lettuce.core.RedisClient;
import io.lettuce.core.RedisURI;
import io.lettuce.core.resource.ClientResources;
import io.lettuce.core.resource.DefaultClientResources;
import io.lettuce.core.api.StatefulRedisConnection;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class LedgerWriterConfig {

    private final String redisHostName;
    private final int redisPort;

    public LedgerWriterConfig() {
        this.redisHostName = System.getenv("LEDGER_ADDR");
        this.redisPort = Integer.valueOf(System.getenv("LEDGER_PORT"));
    }

    @Bean(destroyMethod = "shutdown")
    ClientResources clientResources() {
        return DefaultClientResources.create();
    }

    @Bean(destroyMethod = "shutdown")
    RedisClient redisClient(ClientResources clientResources) {
        return RedisClient.create(clientResources, RedisURI.create(redisHostName, redisPort));
    }

    @Bean(destroyMethod = "close")
    StatefulRedisConnection<String, String> connection(RedisClient redisClient) {
        return redisClient.connect();
    }
}
