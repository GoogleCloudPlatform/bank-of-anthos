package anthos.samples.financedemo.ledgerwriter;

import java.io.Serializable;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
public class Transaction implements Serializable {

    private static final long serialVersionUID = 1L;

    private final long timestampMillis;

    private int fromAccountNum;
    private int fromRoutingNum;
    private int amount;

    public Transaction(int fromAccountNum, int fromRoutingNum, int amount) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.amount = amount;
        this.timestampMillis = System.currentTimeMillis();
    }

    public int getFromAccountNum () {
        return this.fromAccountNum;
    }

    public void setFromAccountNum (Integer fromAccountNum) {
        this.fromAccountNum = fromAccountNum;
    }

    public int getFromRountingNum () {
        return this.fromRoutingNum;
    }

    public void setFromRoutingNum (Integer fromRoutingNum) {
        this.fromRoutingNum = fromRoutingNum;
    }

    public int getAmount() {
        return this.amount;
    }

    public void setAmount(Integer amount) {
        this.amount = amount;
    }

    public long getTimestampMillis() {
        return this.timestampMillis;
    }
}
