package anthos.samples.financedemo.ledgerwriter;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
public class Transaction {

    private static final long serialVersionUID = 1L;

    private final long timestampMillis;

    // Use Strings so Spring and Redis data conversions are way easier.
    private String fromAccountNum;
    private String fromRoutingNum;
    private String toAccountNum;
    private String toRoutingNum;
    private String amount;

    public Transaction(String fromAccountNum, String fromRoutingNum, String toAccountNum,
            String toRoutingNum, String amount) {
        this.fromAccountNum = fromAccountNum;
        this.fromRoutingNum = fromRoutingNum;
        this.toAccountNum = toAccountNum;
        this.toRoutingNum = toRoutingNum;
        this.amount = amount;
        this.timestampMillis = System.currentTimeMillis();
    }

    public String getFromAccountNum() {
        return this.fromAccountNum;
    }

    public void setFromAccountNum(String fromAccountNum) {
        this.fromAccountNum = fromAccountNum;
    }

    public String getFromRoutingNum() {
        return this.fromRoutingNum;
    }

    public void setFromRoutingNum(String fromRoutingNum) {
        this.fromRoutingNum = fromRoutingNum;
    }

    public String getToAccountNum() {
        return this.toAccountNum;
    }

    public void setToAccountNum(String toAccountNum) {
        this.toAccountNum = toAccountNum;
    }

    public String getToRoutingNum() {
        return this.toRoutingNum;
    }

    public void setToRoutingNum(String toRoutingNum) {
        this.toRoutingNum = toRoutingNum;
    }

    public String getAmount() {
        return this.amount;
    }

    public void setAmount(String amount) {
        this.amount = amount;
    }

    public long getTimestampMillis() {
        return this.timestampMillis;
    }
}
