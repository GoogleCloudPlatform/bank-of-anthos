package anthos.samples.bankofanthos.userservice;

import javax.annotation.PreDestroy;
import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the User Service Spring Boot application.
 *
 * Microservice to authenticate users of the application.
 */
@SpringBootApplication
public class UserServiceApplication {
  private static final Logger LOGGER = LogManager.getLogger(UserServiceApplication.class);

  private static final String[] EXPECTED_ENV_VARS = {
//      "VERSION",
//      "TOKEN_EXPIRY_SECONDS",
//      "PRIV_KEY_PATH",
//      "PUB_KEY_PATH",
  };

  public static void main(String[] args) {
    // Check that all required environment variables are set.
    for (String v : EXPECTED_ENV_VARS) {
      String value = System.getenv(v);
      if (value == null) {
        LOGGER.fatal(String.format("%s environment variable not set", v));
        System.exit(1);
      }
    }

    SpringApplication.run(UserServiceApplication.class, args);
    LOGGER.log(Level.forName("STARTUP", Level.INFO.intLevel()),
        String.format("Started UserService service. Log level is: %s",
            LOGGER.getLevel().toString()));
  }

  @PreDestroy
  public void destroy() {
    LOGGER.info("LedgerWriter service shutting down");
  }
}
