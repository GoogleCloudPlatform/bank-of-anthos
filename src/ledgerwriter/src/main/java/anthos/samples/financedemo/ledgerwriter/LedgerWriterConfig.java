package anthos.samples.financedemo.ledgerwriter;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.jedis.JedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import javax.annotation.PostConstruct;

@Configuration
public class LedgerWriterConfig {

    private String redisHostName;
    private String redisPort;

    @PostConstruct
    private void loadEnvironmentVariables() {
        redisHostName = System.getenv("LEDGER_ADDR");
        if (redisHostName == null || redisHostName.isEmpty()) {
            throw new RuntimeException("No address provided for Redis backend");
        }

        redisPort = System.getenv("LEDGER_PORT");
        if (redisPort == null || redisPort.isEmpty()) {
            throw new RuntimeException("No port provided for Redis backend");
        }
    }

    @Bean
    public JedisConnectionFactory connectionFactory() {
        JedisConnectionFactory connectionFactory = new JedisConnectionFactory();
        connectionFactory.setHostName(redisHostName);
        connectionFactory.setPort(Integer.parseInt(redisPort));
        return connectionFactory;
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> redisTemplate = new RedisTemplate<String, Object>();
        redisTemplate.setConnectionFactory(connectionFactory());
                redisTemplate.setKeySerializer(new StringRedisSerializer());
        return redisTemplate;
    }
}
