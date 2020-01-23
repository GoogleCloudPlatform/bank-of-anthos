package anthos.samples.financedemo.ledgerwriter;

import java.io.Serializable;

/**
 * Defines a banking transaction.
 */
public class Transaction implements Serializable {

    private static final long serialVersionUID = 1L;

    private final String fromAccountNum;
    private final String fromRoutingNum;
    private final int amount;
    private final long timestamp;

    public Transaction(String fromAccountNum, String fromRoutingNum, int amount) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.amount = amount;
        this.timestamp = System.currentTimeMillis();
    }

    public String getFromAccountNum () {
        return this.fromAccountNum;
    }

    public String getFromRountingNum () {
        return this.fromRoutingNum;
    }

    public int getAmount() {
        return this.amount;
    }

    public long getTimestamp() {
        return this.timestamp;
    }
}
