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

import java.nio.charset.Charset;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import javax.validation.Valid;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/**
 * Implements the REST endpoints of the User Service.
 */
@RestController
public class UserServiceController {

  private static final Logger LOGGER = LogManager.getLogger(UserServiceController.class);
  private static final String READINESS_CODE = "ok";
  private static final BCryptPasswordEncoder BCRYPT_ENCODER = new BCryptPasswordEncoder();
  private static final DateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd");

  private final UserRepository userRepository;
  private final JwtTokenProvider jwtTokenProvider;

  @Value("${user-service.version}")
  private String version;

  public UserServiceController(
      UserRepository userRepository, JwtTokenProvider jwtTokenProvider) {
    this.userRepository = userRepository;
    this.jwtTokenProvider = jwtTokenProvider;
  }

  /**
   * Readiness probe endpoint.
   *
   * @return HTTP Status 200 if server is ready to receive requests.
   */
  @GetMapping("/ready")
  @ResponseStatus(HttpStatus.OK)
  public ResponseEntity<String> ready() {
    return new ResponseEntity<>(READINESS_CODE, HttpStatus.OK);
  }

  /**
   * Validates requests to create new users and create a user record.
   *
   * Fails if that username already exists.
   */
  @PostMapping("/users")
  public ResponseEntity<String> users(
      @Valid @RequestBody CreateUserRequest request) {

    if (!request.password.equals(request.passwordRepeat)) {
      return new ResponseEntity<>(
          "Error: Passwords do not match.", HttpStatus.BAD_REQUEST);
    }

    if (userRepository.findFirstByUsername(request.username) != null) {
      return new ResponseEntity<>(
          "Error: Username already exists.", HttpStatus.BAD_REQUEST);
    }

    try {
      User user = createUser(request);
      userRepository.save(user);
      LOGGER.info("Successfully created user: " + user.getUsername());
      return new ResponseEntity<>(HttpStatus.CREATED);
    } catch (Exception e) {
      LOGGER.error("Failed to create new user.", e);
      return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
    }
  }

  /**
   * Perform login with the provided {@code username} and {@code password};
   * if valid will return a JWT token for authentication.
   */
  @GetMapping("/login")
  public ResponseEntity<String> login(
      @RequestParam String username, @RequestParam String password) {

    User user = userRepository.findFirstByUsername(username);
    if (user == null) {
      return new ResponseEntity<>("Error: User does not exist.", HttpStatus.BAD_REQUEST);
    }

    if (!BCRYPT_ENCODER.matches(
        password, new String(user.getPasshash(), Charset.defaultCharset()))) {
      return new ResponseEntity<>("Error: Incorrect password.", HttpStatus.BAD_REQUEST);
    }

    String jsonToken =
        new JSONObject().put("token", jwtTokenProvider.createJwtToken(user)).toString();
    return new ResponseEntity<>(jsonToken, HttpStatus.OK);
  }

  @GetMapping("/version")
  public ResponseEntity<String> version() {
    return new ResponseEntity<>(version, HttpStatus.OK);
  }

  /**
   * Creates a {@link User} record from the provided {@link CreateUserRequest}.
   */
  private User createUser(CreateUserRequest request) throws ParseException {
    return new User(
        request.username,
        BCRYPT_ENCODER.encode(request.password).getBytes(),
        request.firstname,
        request.lastname,
        parseDate(request.birthday),
        request.timezone,
        request.address,
        request.state,
        request.zip,
        request.ssn);
  }

  private static Date parseDate(String dateString) throws ParseException {
    // If we get a date using slashes, convert it to using dashes.
    dateString = dateString.replace('/', '-');
    return DATE_FORMAT.parse(dateString);
  }
}
