package anthos.samples.bankofanthos.userservice;

import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration;

/**
 * Entry point for the User Service Spring Boot application.
 *
 * Microservice to authenticate users of the application.
 */
@SpringBootApplication(exclude = { SecurityAutoConfiguration.class })
public class UserServiceApplication {
  private static final Logger LOGGER = LogManager.getLogger(UserServiceApplication.class);

  public static void main(String[] args) {
    SpringApplication.run(UserServiceApplication.class, args);
    LOGGER.log(Level.forName("STARTUP", Level.INFO.intLevel()),
        String.format("Started UserService service. Log level is: %s", LOGGER.getLevel().toString()));
  }

}
