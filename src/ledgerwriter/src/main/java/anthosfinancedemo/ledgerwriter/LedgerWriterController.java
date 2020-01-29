package anthosfinancedemo.ledgerwriter;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;


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
  public final void addTransaction(@RequestHeader("Authorization") String bearerToken,
                                   @RequestBody Transaction transaction) throws IOException,
                                   NoSuchAlgorithmException, InvalidKeySpecException {
    if (bearerToken != null && bearerToken.startsWith("Bearer ")){
      bearerToken = bearerToken.split("Bearer ")[1];
    }
    System.out.println(bearerToken);

    String pubKeyPath = System.getenv("PUB_KEY_PATH");
    System.out.println(pubKeyPath);
    byte[] pubKeyBytes  = Files.readAllBytes(Paths.get(pubKeyPath));
    String pubKeyStr = new String (pubKeyBytes);
    //pubKeyStr = pubKeyStr.split(" ")[1];
    System.out.println(pubKeyStr);

    pubKeyStr = pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
    pubKeyStr = pubKeyStr.replaceAll("\\s", "");
    System.out.println(pubKeyStr);
    pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);

    KeyFactory kf = KeyFactory.getInstance("RSA");
    X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(pubKeyBytes);
    RSAPublicKey pubKey = (RSAPublicKey) kf.generatePublic(keySpecX509);

    try {
        Algorithm algorithm = Algorithm.RSA256(pubKey, null);
        JWTVerifier verifier = JWT.require(algorithm).build();
        DecodedJWT jwt = verifier.verify(bearerToken);
        System.out.println("success");
    } catch (JWTVerificationException exception){
        //Invalid signature/claims
        System.out.println("error");
        System.out.println(exception);
    }
    // TODO: Do stuff
    //
    // Get the auth header.
    // Authenticate the jwt.
    // Extract the account id from the jwt.
    //
    // Perform validation checks
    // Get current balance, check against request
    //
    // Submit Transaction to repository
  }

}
