package anthos.samples.bankofanthos.userservice;

import com.fasterxml.jackson.annotation.JsonProperty;
import javax.validation.constraints.NotBlank;

public class CreateUserRequest {

  @NotBlank
  private String username;

  @NotBlank
  private String password;

  @NotBlank
  @JsonProperty("password-repeat")
  private String passwordRepeat;

  @NotBlank
  private String firstname;

  @NotBlank
  private String lastname;

  @NotBlank
  private String birthday;

  @NotBlank
  private String timezone;

  @NotBlank
  private String address;

  @NotBlank
  private String state;

  @NotBlank
  private String zip;

  @NotBlank
  private String ssn;

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public String getPassword() {
    return password;
  }

  public void setPassword(String password) {
    this.password = password;
  }

  public String getPasswordRepeat() {
    return passwordRepeat;
  }

  public void setPasswordRepeat(String passwordRepeat) {
    this.passwordRepeat = passwordRepeat;
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

  public String getBirthday() {
    return birthday;
  }

  public void setBirthday(String birthday) {
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
    return "CreateUserRequest{" +
        "username='" + username + '\'' +
        ", password='" + password + '\'' +
        ", passwordRepeat='" + passwordRepeat + '\'' +
        ", firstName='" + firstname + '\'' +
        ", lastName='" + lastname + '\'' +
        ", birthday='" + birthday + '\'' +
        ", timezone='" + timezone + '\'' +
        ", address='" + address + '\'' +
        ", state='" + state + '\'' +
        ", zipCode='" + zip + '\'' +
        ", ssn='" + ssn + '\'' +
        '}';
  }
}
