package io.brissach.probuild.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class RequestSigner {

  private final String secret;

  public RequestSigner(String secret) {
    this.secret = secret;
  }

  public String sign(String timestamp, String requestId, byte[] body) {
    try {
      var digest = MessageDigest.getInstance("SHA-256");
      var bodyHash = HexFormat.of().formatHex(digest.digest(body));
      var message = timestamp + ":" + requestId + ":" + bodyHash;
      var mac = Mac.getInstance("HmacSHA256");
      mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
      return HexFormat.of().formatHex(mac.doFinal(message.getBytes(StandardCharsets.UTF_8)));
    } catch (Exception ex) {
      throw new IllegalStateException("failed to sign request", ex);
    }
  }
}
