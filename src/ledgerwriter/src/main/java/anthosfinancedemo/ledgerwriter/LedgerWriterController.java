package anthosfinancedemo.ledgerwriter;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.http.ResponseEntity;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;


@RestController
public class LedgerWriterController {

  private final JWTVerifier verifier;

  public LedgerWriterController() 
      throws IOException, NoSuchAlgorithmException, InvalidKeySpecException  {
    // load public key from file
    String pubKeyPath = System.getenv("PUB_KEY_PATH");
    String pubKeyStr  = new String(Files.readAllBytes(Paths.get(pubKeyPath)));
    pubKeyStr = pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceAll("\\s", "");
    byte[] pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);
    KeyFactory kf = KeyFactory.getInstance("RSA");
    X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(pubKeyBytes);
    RSAPublicKey publicKey = (RSAPublicKey) kf.generatePublic(keySpecX509);
    // set up verifier
    Algorithm algorithm = Algorithm.RSA256(publicKey, null);
    this.verifier = JWT.require(algorithm).build();
  }

  /**
   * returns 200 when service is alive
   * used for readiness probe.
   */
  @GetMapping("/ready")
  @ResponseStatus(HttpStatus.OK)
  public final String readiness() {
      return "ok";
  }

  @PostMapping("/new_transaction")
  public final ResponseEntity<?> addTransaction(@RequestHeader("Authorization") String bearerToken,
        @RequestBody Transaction transaction) {
    if (bearerToken != null && bearerToken.startsWith("Bearer ")){
      bearerToken = bearerToken.split("Bearer ")[1];
    }
    try {
      DecodedJWT jwt = this.verifier.verify(bearerToken);
      String initiatorAcct = jwt.getClaim("acct").asString();
      System.out.println("transaction: " + transaction);
      return new ResponseEntity<String>("ok", HttpStatus.CREATED);
    } catch (JWTVerificationException e){
      return new ResponseEntity<String>("", HttpStatus.UNAUTHORIZED);
    }

  }
}
