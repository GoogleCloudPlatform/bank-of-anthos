package anthos.samples.bankofanthos.userservice;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.util.Date;

/**
 * Represents a User record in the Bank of Anthos.
 */
@Entity
public class User {

  @Id
  @GeneratedValue
  private long id;
  private String username;
  private String passhash;
  private String firstName;
  private String lastName;
  private Date birthday;
  private String timezone;
  private String address;
  private String state;
  private int zipCode;
  private String ssn;

  public User(
      String username, String passhash, String firstName, String lastName,
      Date birthday, String timezone, String address, String state,
      int zipCode, String ssn) {

    this.username = username;
    this.passhash = passhash;
    this.firstName = firstName;
    this.lastName = lastName;
    this.birthday = birthday;
    this.timezone = timezone;
    this.address = address;
    this.state = state;
    this.zipCode = zipCode;
    this.ssn = ssn;
  }

  // Default constructor used by Spring Data JPA.
  User() {

  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public String getPasshash() {
    return passhash;
  }

  public void setPasshash(String passhash) {
    this.passhash = passhash;
  }

  public String getFirstName() {
    return firstName;
  }

  public void setFirstName(String firstName) {
    this.firstName = firstName;
  }

  public String getLastName() {
    return lastName;
  }

  public void setLastName(String lastName) {
    this.lastName = lastName;
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

  public int getZipCode() {
    return zipCode;
  }

  public void setZipCode(int zipCode) {
    this.zipCode = zipCode;
  }

  public String getSsn() {
    return ssn;
  }

  public void setSsn(String ssn) {
    this.ssn = ssn;
  }
}
