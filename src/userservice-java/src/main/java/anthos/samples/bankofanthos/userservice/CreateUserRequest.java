package anthos.samples.bankofanthos.userservice;

import com.fasterxml.jackson.annotation.JsonProperty;

import javax.validation.constraints.NotBlank;

/**
 * Request object which describes the parameters provided in the POST request to create a user
 * for the User Service.
 */
public class CreateUserRequest {

  @NotBlank
  public final String username;

  @NotBlank
  public final String password;

  @NotBlank
  @JsonProperty("password-repeat")
  public final String passwordRepeat;

  @NotBlank
  public final String firstname;

  @NotBlank
  public final String lastname;

  @NotBlank
  public final String birthday;

  @NotBlank
  public final String timezone;

  @NotBlank
  public final String address;

  @NotBlank
  public final String state;

  @NotBlank
  public final String zip;

  @NotBlank
  public final String ssn;

  public CreateUserRequest(String username,
      String password,
      String passwordRepeat,
      String firstname, String lastname,
      String birthday, String timezone,
      String address, String state,
      String zip, String ssn) {
    this.username = username;
    this.password = password;
    this.passwordRepeat = passwordRepeat;
    this.firstname = firstname;
    this.lastname = lastname;
    this.birthday = birthday;
    this.timezone = timezone;
    this.address = address;
    this.state = state;
    this.zip = zip;
    this.ssn = ssn;
  }

  @Override
  public String toString() {
    return "CreateUserRequest{"
            + "username='" + username + '\''
            + ", password='" + password + '\''
            + ", passwordRepeat='" + passwordRepeat + '\''
            + ", firstName='" + firstname + '\''
            + ", lastName='" + lastname + '\''
            + ", birthday='" + birthday + '\''
            + ", timezone='" + timezone + '\''
            + ", address='" + address + '\''
            + ", state='" + state + '\''
            + ", zipCode='" + zip + '\''
            + ", ssn='" + ssn + '\''
            + '}';
  }
}
