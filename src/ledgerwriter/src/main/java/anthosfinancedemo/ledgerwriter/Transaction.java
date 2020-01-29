package anthosfinancedemo.ledgerwriter;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 */
public class Transaction {

    @JsonProperty("from_account_num")
    private String fromAccountNum;
    @JsonProperty("from_routing_num")
    private String fromRoutingNum;
    @JsonProperty("to_account_num")
    private String toAccountNum;
    @JsonProperty("to_routing_num")
    private String toRoutingNum;
    private int amount;

    public Transaction(String fromAccountNum, String fromRoutingNum,
        String toAccountNum, String toRoutingNum, int amount) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.toAccountNum = toAccountNum;
        this.toRoutingNum = toRoutingNum;
        this.amount = amount;
    }

    public final String getFromAccountNum () {
        return this.fromAccountNum;
    }

    public final String getFromRountingNum () {
        return this.fromRoutingNum;
    }

    public final String getToAccountNum () {
        return this.toAccountNum;
    }

    public final String getToRountingNum () {
        return this.toRoutingNum;
    }

    public final int getAmount() {
        return this.amount;
    }

    public String toString() {
        return String.format("$%d: %s->%s", amount/100, fromAccountNum, toAccountNum);
    }
}
