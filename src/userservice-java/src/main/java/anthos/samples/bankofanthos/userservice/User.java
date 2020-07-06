package anthos.samples.bankofanthos.userservice;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.util.Date;

/**
 * Represents a User record in the Bank of Anthos.
 */
@Entity(name = "users")
public class User {

  @Id
  @GeneratedValue
  private long accountid;
  private String username;
  private byte[] passhash;
  private String firstname;
  private String lastname;
  private Date birthday;
  private String timezone;
  private String address;
  private String state;
  private String zip;
  private String ssn;

  public User(
      String username, byte[] passhash, String firstname, String lastname,
      Date birthday, String timezone, String address, String state,
      String zip, String ssn) {

    this.username = username;
    this.passhash = passhash;
    this.firstname = firstname;
    this.lastname = lastname;
    this.birthday = birthday;
    this.timezone = timezone;
    this.address = address;
    this.state = state;
    this.zip = zip;
    this.ssn = ssn;
  }

  // Default constructor used by Spring Data JPA.
  User() {

  }

  public long getAccountid() {
    return accountid;
  }

  public void setAccountid(long accountid) {
    this.accountid = accountid;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public byte[] getPasshash() {
    return passhash;
  }

  public void setPasshash(byte[] passhash) {
    this.passhash = passhash;
  }

  public String getFirstname() {
    return firstname;
  }

  public void setFirstname(String firstname) {
    this.firstname = firstname;
  }

  public String getLastname() {
    return lastname;
  }

  public void setLastname(String lastname) {
    this.lastname = lastname;
  }

  public Date getBirthday() {
    return birthday;
  }

  public void setBirthday(Date birthday) {
    this.birthday = birthday;
  }

  public String getTimezone() {
    return timezone;
  }

  public void setTimezone(String timezone) {
    this.timezone = timezone;
  }

  public String getAddress() {
    return address;
  }

  public void setAddress(String address) {
    this.address = address;
  }

  public String getState() {
    return state;
  }

  public void setState(String state) {
    this.state = state;
  }

  public String getZip() {
    return zip;
  }

  public void setZip(String zip) {
    this.zip = zip;
  }

  public String getSsn() {
    return ssn;
  }

  public void setSsn(String ssn) {
    this.ssn = ssn;
  }

  @Override
  public String toString() {
    return "User{" +
        "accountid=" + accountid +
        ", username='" + username + '\'' +
        ", passhash='" + passhash + '\'' +
        ", firstName='" + firstname + '\'' +
        ", lastName='" + lastname + '\'' +
        ", birthday=" + birthday +
        ", timezone='" + timezone + '\'' +
        ", address='" + address + '\'' +
        ", state='" + state + '\'' +
        ", zipCode=" + zip +
        ", ssn='" + ssn + '\'' +
        '}';
  }
}
