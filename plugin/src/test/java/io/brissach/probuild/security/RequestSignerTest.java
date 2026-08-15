package io.brissach.probuild.security;

import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertNotEquals;

class RequestSignerTest {

  @Test
  void signaturesDifferForDifferentBodies() {
    var signer = new RequestSigner("secret-value-1234567890");
    var first = signer.sign("1", "req", "{\"prompt\":\"a\"}".getBytes(StandardCharsets.UTF_8));
    var second = signer.sign("1", "req", "{\"prompt\":\"b\"}".getBytes(StandardCharsets.UTF_8));
    assertNotEquals(first, second);
  }
}
