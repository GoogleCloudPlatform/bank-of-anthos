package anthosfinancedemo.ledgerwriter;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 */
public class Transaction {

    @JsonProperty("from_account_num")
    public String fromAccountNum;
    @JsonProperty("from_routing_num")
    public String fromRoutingNum;
    @JsonProperty("to_account_num")
    public String toAccountNum;
    @JsonProperty("to_routing_num")
    public String toRoutingNum;
    @JsonProperty("amount")
    public int amount;
    public long date;

    public String toString() {
        return String.format("$%d: %s->%s", amount/100, fromAccountNum, toAccountNum);
    }
}
