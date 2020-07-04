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
    claims.put("acct", user.getId());
    claims.put("name", user.getFirstName() + " " + user.getLastName());
    claims.put("iat", currentTime.toString());
    claims.put("exp", currentTime.plusSeconds(expiryTimeSeconds).toString());

    return claims;
  }
}
