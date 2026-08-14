package io.brissach.probuild.world;

import io.brissach.probuild.structure.Structure;
import org.bukkit.Location;

public interface AbstractWorld {
  int placeStructure(Location origin, Structure structure);

  String id();
}
