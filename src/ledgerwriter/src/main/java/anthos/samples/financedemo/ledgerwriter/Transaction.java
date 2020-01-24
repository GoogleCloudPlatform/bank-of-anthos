package anthos.samples.financedemo.ledgerwriter;

import java.io.Serializable;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
public class Transaction implements Serializable {

    private static final long serialVersionUID = 1L;

    private final String fromAccountNum;
    private final String fromRoutingNum;
    private final int amount;
    private final long timestampMillis;

    public Transaction(String fromAccountNum, String fromRoutingNum, int amount) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.amount = amount;
        this.timestampMillis = System.currentTimeMillis();
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

    public long getTimestampMillis() {
        return this.timestampMillis;
    }
}
