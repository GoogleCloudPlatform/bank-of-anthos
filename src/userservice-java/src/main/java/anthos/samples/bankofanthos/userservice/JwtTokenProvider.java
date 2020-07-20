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

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.security.PrivateKey;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Helper class which creates JWT tokens.
 */
public final class JwtTokenProvider {

  private final PrivateKey jwtSecret;

  private final long expiryTimeSeconds;

  /**
   * Constructs the JwtTokenProvider
   *
   * @param expiryTimeSeconds duration in seconds before the JWT token expires.
   */
  public JwtTokenProvider(PrivateKey jwtSecret, long expiryTimeSeconds) {
    this.jwtSecret = jwtSecret;
    this.expiryTimeSeconds = expiryTimeSeconds;
  }

  /**
   * Creates a JWT token for the provided {@link User}.
   * @param user the logged in user to create a JWT token for.
   */
  public String createJwtToken(User user) {
    return Jwts.builder()
        .setClaims(getJwtClaimsMap(user))
        .signWith(SignatureAlgorithm.RS256, jwtSecret)
        .compact();
  }

  /**
   * Creates the claims to be encoded in the JWT token.
   */
  private Map<String, Object> getJwtClaimsMap(User user) {
    Instant currentTime = Instant.now();

    Map<String, Object> claims = new HashMap<>();
    claims.put("user", user.getUsername());
    claims.put("acct", Long.toString(user.getAccountid()));
    claims.put("name", user.getFirstname() + " " + user.getLastname());
    claims.put("iat", currentTime.getEpochSecond());
    claims.put("exp", currentTime.getEpochSecond() + expiryTimeSeconds);

    return claims;
  }
}
