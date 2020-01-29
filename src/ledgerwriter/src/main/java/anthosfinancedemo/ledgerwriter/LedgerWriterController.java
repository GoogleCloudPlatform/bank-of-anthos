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
        @RequestBody Transaction transaction) throws IOException, NoSuchAlgorithmException,
        InvalidKeySpecException, JWTVerificationException{
    if (bearerToken != null && bearerToken.startsWith("Bearer ")){
      bearerToken = bearerToken.split("Bearer ")[1];
    }

    DecodedJWT jwt = verifyToken(bearerToken);
    String initiatorAcct = jwt.getClaim("acct").asString();
    System.out.println("transaction: " + transaction);
    return new ResponseEntity<String>("ok", HttpStatus.CREATED);
  }

  private final DecodedJWT verifyToken(String token)  throws IOException, NoSuchAlgorithmException,
        InvalidKeySpecException, JWTVerificationException{
    String pubKeyPath = System.getenv("PUB_KEY_PATH");
    byte[] pubKeyBytes  = Files.readAllBytes(Paths.get(pubKeyPath));
    String pubKeyStr = new String (pubKeyBytes);
    pubKeyStr = pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceAll("\\s", "");
    pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);

    KeyFactory kf = KeyFactory.getInstance("RSA");
    X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(pubKeyBytes);
    RSAPublicKey pubKey = (RSAPublicKey) kf.generatePublic(keySpecX509);

    Algorithm algorithm = Algorithm.RSA256(pubKey, null);
    JWTVerifier verifier = JWT.require(algorithm).build();
    return verifier.verify(token);
  }

}
