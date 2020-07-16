package anthos.samples.bankofanthos.userservice;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.spec.PKCS8EncodedKeySpec;

@Configuration
public class UserServiceConfiguration {

  @Value("${user-service.priv-key-path}")
  private String privateKeyPath;

  @Value("${user-service.token-expiry-seconds}")
  private int tokenExpirySeconds;

  @Bean
  public JwtTokenProvider jwtTokenProvider() throws Exception {
    byte[] keyBytes = Files.readAllBytes(Paths.get(privateKeyPath));

    KeyFactory keyFactory = KeyFactory.getInstance("RSA");
    PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(keyBytes);
    PrivateKey key = keyFactory.generatePrivate(spec);
    return new JwtTokenProvider(key, tokenExpirySeconds);
  }
}
