package anthosfinancedemo.ledgerwriter;

/**
 * Defines a banking transaction.
 */
public class Transaction {

    private final String fromAccountNum;
    private final String fromRoutingNum;
    private final int amount;
    private final long date;

    public Transaction(String fromAccountNum, String fromRoutingNum, int amount, long date) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.amount = amount;
        this.date = date;
    }

    public final String getFromAccountNum () {
        return this.fromAccountNum;
    }

    public final String getFromRountingNum () {
        return this.fromRoutingNum;
    }

    public final int getAmount() {
        return this.date;
    }

    public final long getDate() {
        return this.date;
    }
}
