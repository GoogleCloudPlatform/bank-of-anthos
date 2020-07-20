/*
 * Copyright 2020, Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
        String.format("Started UserService service. Log level is: %s",
            LOGGER.getLevel().toString()));
  }

}
