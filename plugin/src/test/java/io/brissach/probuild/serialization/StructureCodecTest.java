package io.brissach.probuild.serialization;

import com.google.gson.JsonObject;
import io.brissach.probuild.structure.BlockPlacement;
import io.brissach.probuild.structure.Structure;
import java.util.List;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class StructureCodecTest {

  @Test
  void roundTrip() {
    var codec = new StructureCodec();
    var structure = new Structure(
      2,
      2,
      2,
      List.of(new BlockPlacement(0, 0, 0, "stone"))
    );
    JsonObject encoded = codec.encode(structure);
    var decoded = codec.decode(encoded);
    assertEquals(1, decoded.blockCount());
    assertEquals("stone", decoded.blocks().getFirst().blockId());
  }
}
