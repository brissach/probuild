package io.brissach.probuild.util;

import org.bukkit.Location;

public final class Locations {

  private Locations() {}

  public static Location floorUnder(org.bukkit.entity.Player player) {
    var location = player.getLocation().clone();
    location.setY(Math.floor(location.getY()));
    return location;
  }
}
