package io.brissach.probuild.structure;

import io.brissach.probuild.Context;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;

class StructureValidatorTest {

  @Test
  void rejectsUnsupportedBlock() {
    var context = new Context(
      "http://localhost:8000",
      "key",
      "secret",
      1000,
      32,
      32,
      32,
      2,
      1000,
      "auto"
    );
    var validator = new StructureValidator(context);
    var structure = new Structure(
      4,
      4,
      4,
      List.of(new BlockPlacement(0, 0, 0, "netherite_block"))
    );
    assertFalse(validator.validate(structure).isValid());
  }
}
