package anthosfinancedemo.ledgerwriter;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
public class LedgerWriterController {

  @PostMapping("/new_transaction")
  public final void addTransaction(@RequestBody Transaction transaction) {
    // TODO: Do stuff
    //
    // Get the auth header.
    // Authenticate the jwt.
    // Extract the account id from the jwt.
    //
    // Perform validation checks
    // Get current balance, check against request
    //
    // Submit Transaction to repository
  }

}
