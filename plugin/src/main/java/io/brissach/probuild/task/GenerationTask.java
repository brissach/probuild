package io.brissach.probuild.task;

import io.brissach.probuild.api.ApiRequest;
import io.brissach.probuild.generation.GenerationRequest;
import io.brissach.probuild.generation.GenerationService;
import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

public final class GenerationTask implements Runnable {

  private final JavaPlugin plugin;
  private final GenerationService.Snapshot bindings;
  private final Player player;
  private final GenerationRequest request;
  private final Runnable onComplete;

  public GenerationTask(
    JavaPlugin plugin,
    GenerationService.Snapshot bindings,
    Player player,
    GenerationRequest request,
    Runnable onComplete
  ) {
    this.plugin = plugin;
    this.bindings = bindings;
    this.player = player;
    this.request = request;
    this.onComplete = onComplete;
  }

  @Override
  public void run() {
    try {
      var apiRequest = new ApiRequest(
        request.prompt(),
        request.seed(),
        request.width(),
        request.height(),
        request.depth(),
        0.8,
        50
      );
      var response = bindings.client().generate(apiRequest);
      var validation = bindings.validator().validate(response.structure());
      if (!validation.isValid()) {
        notifyPlayer("Probuild rejected structure: " + validation.message().orElse("invalid"));
        return;
      }
      Bukkit.getScheduler().runTask(plugin, () -> {
        if (!player.isOnline()) {
          return;
        }
        var placement = bindings.placer().place(request.origin(), response.structure());
        if (placement.success()) {
          player.sendMessage("Probuild placed " + placement.placedBlocks() + " blocks.");
        } else {
          player.sendMessage("Probuild failed to place structure: " + placement.message());
        }
      });
    } catch (Exception ex) {
      notifyPlayer("Probuild generation failed: " + ex.getMessage());
    } finally {
      onComplete.run();
    }
  }

  private void notifyPlayer(String message) {
    Bukkit.getScheduler().runTask(plugin, () -> {
      if (player.isOnline()) {
        player.sendMessage(message);
      }
    });
  }
}
