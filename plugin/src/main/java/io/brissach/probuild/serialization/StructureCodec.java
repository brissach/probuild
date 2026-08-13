package io.brissach.probuild.serialization;

import com.google.gson.JsonObject;
import io.brissach.probuild.structure.BlockPlacement;
import io.brissach.probuild.structure.Structure;
import java.util.ArrayList;

public final class StructureCodec {

  public Structure decode(JsonObject json) {
    var width = json.get("width").getAsInt();
    var height = json.get("height").getAsInt();
    var depth = json.get("depth").getAsInt();
    var blocks = new ArrayList<BlockPlacement>();
    for (var element : json.getAsJsonArray("blocks")) {
      var block = element.getAsJsonObject();
      blocks.add(new BlockPlacement(
        block.get("x").getAsInt(),
        block.get("y").getAsInt(),
        block.get("z").getAsInt(),
        block.get("id").getAsString()
      ));
    }
    return new Structure(width, height, depth, blocks);
  }

  public JsonObject encode(Structure structure) {
    var json = new JsonObject();
    json.addProperty("width", structure.width());
    json.addProperty("height", structure.height());
    json.addProperty("depth", structure.depth());
    var blocks = new com.google.gson.JsonArray();
    structure.blocks().forEach(block -> {
      var entry = new JsonObject();
      entry.addProperty("x", block.x());
      entry.addProperty("y", block.y());
      entry.addProperty("z", block.z());
      entry.addProperty("id", block.blockId());
      blocks.add(entry);
    });
    json.add("blocks", blocks);
    return json;
  }
}
