package anthosfinancedemo.ledgerwriter;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines an account balance.
 */
public class Balance {

    @JsonProperty("balance")
    public int amount;

    public String toString() {
        return String.format("$%d", amount);
    }
}
