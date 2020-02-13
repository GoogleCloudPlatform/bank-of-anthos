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

package anthos.samples.financedemo.common;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;

/**
 * Tools for authentication.
 */
public final class AuthTools {

    /**
     * Create a JWT verifier from a public key text file.
     *
     * @param filePath path to text file of public key
     * @return a JWTVerifier object
     */
    public static JWTVerifier newJWTVerifierFromFile(String filePath) {
        // load public key from file
        try {
            String pubKeyStr =
                    new String(Files.readAllBytes(Paths.get(filePath)));
            // trim text
            pubKeyStr =
                    pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
            pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
            pubKeyStr = pubKeyStr.replaceAll("\\s", "");

            // perform encoding
            byte[] pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);
            KeyFactory kf = KeyFactory.getInstance("RSA");
            X509EncodedKeySpec keySpecX509 =
                    new X509EncodedKeySpec(pubKeyBytes);
            RSAPublicKey publicKey =
                    (RSAPublicKey) kf.generatePublic(keySpecX509);

            // set up verifier
            Algorithm algorithm = Algorithm.RSA256(publicKey, null);
            return JWT.require(algorithm).build();
        } catch (IOException e) {
            String message =
                    "Could not read public key from given file: " + filePath;
            throw new IllegalArgumentException(message, e);
        } catch (NoSuchAlgorithmException e) {
            String message =
                    "The RSA cryptosystem is not available on this host.";
            throw new IllegalStateException(message, e);
        } catch (InvalidKeySpecException e) {
            String message =
                    "Public key file must use X.509 standard formatting.";
            throw new IllegalArgumentException(message, e);
        }
    }
}
