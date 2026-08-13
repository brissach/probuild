package io.brissach.probuild.structure;

import io.brissach.probuild.world.AbstractWorld;
import org.bukkit.Location;

public final class StructurePlacer {

  private final AbstractWorld world;
  private final StructureValidator validator;

  public StructurePlacer(AbstractWorld world, StructureValidator validator) {
    this.world = world;
    this.validator = validator;
  }

  public AbstractWorld world() {
    return world;
  }

  public PlacementResult place(Location origin, Structure structure) {
    var validation = validator.validate(structure);
    if (!validation.isValid()) {
      return PlacementResult.failed(validation.message().orElse("invalid structure"));
    }
    var placed = world.placeStructure(origin, structure);
    return PlacementResult.success(placed);
  }

  public record PlacementResult(boolean success, int placedBlocks, String message) {
    public static PlacementResult success(int placedBlocks) {
      return new PlacementResult(true, placedBlocks, "");
    }

    public static PlacementResult failed(String message) {
      return new PlacementResult(false, 0, message);
    }
  }
}
