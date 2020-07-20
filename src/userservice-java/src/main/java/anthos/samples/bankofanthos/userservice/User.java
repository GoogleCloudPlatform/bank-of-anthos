/*
 * Copyright 2020, Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package anthos.samples.bankofanthos.userservice;

import java.util.Date;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import org.hibernate.annotations.GenericGenerator;

/**
 * Represents a User record in the Bank of Anthos.
 */
@Entity(name = "users")
public class User {

  @Id
  @GeneratedValue(generator = "randomLong")
  @GenericGenerator(
      name = "randomLong",
      strategy = "anthos.samples.bankofanthos.userservice.AccountIdGenerator")
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
    return "User{"
        + "accountid=" + accountid
        + ", username='" + username + '\''
        + ", passhash='" + passhash + '\''
        + ", firstName='" + firstname + '\''
        + ", lastName='" + lastname + '\''
        + ", birthday=" + birthday
        + ", timezone='" + timezone + '\''
        + ", address='" + address + '\''
        + ", state='" + state + '\''
        + ", zipCode=" + zip
        + ", ssn='" + ssn + '\''
        + '}';
  }
}
