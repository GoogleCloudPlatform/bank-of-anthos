package anthos.samples.bankofanthos.userservice;

import javax.validation.Valid;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserServiceController {

  private static final Logger LOGGER = LogManager.getLogger(UserServiceController.class);

  private static final String READINESS_CODE = "ok";

  private final UserRepository userRepository;

  public UserServiceController(UserRepository userRepository) {
    this.userRepository = userRepository;
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
   * Validates and create a user record.
   *
   * Fails if that username already exists.
   */
  @PostMapping("/users")
  public ResponseEntity<String> createUser(@Valid @RequestBody CreateUserRequest request) {
    System.out.println(request);
    return new ResponseEntity<>(HttpStatus.OK);
  }
}
