package io.brissach.probuild.command;

import io.brissach.probuild.Context;
import io.brissach.probuild.ProbuildPlugin;
import io.brissach.probuild.generation.GenerationRequest;
import io.brissach.probuild.generation.GenerationService;
import io.brissach.probuild.util.Locations;
import io.brissach.probuild.util.command.Commands;

public final class ProbuildCommand {

  private ProbuildCommand() {}

  public static Commands create(
    ProbuildPlugin plugin,
    GenerationService generationService,
    Context context
  ) {
    return Commands.builder()
      .usage("Usage: /probuild <create|reload|status> ...")
      .command("create", "probuild.create", ctx -> {
        var player = ctx.requirePlayer();
        ctx.requireArgs(2, "Usage: /probuild create <prompt>");
        var prompt = ctx.joinArgs(1);
        generationService.beginGeneration(
          player,
          new GenerationRequest(
            prompt,
            Locations.floorUnder(player),
            context.maxWidth(),
            context.maxHeight(),
            context.maxDepth(),
            player.getUniqueId().getMostSignificantBits()
          )
        );
      })
      .command("reload", "probuild.reload", ctx -> {
        plugin.reloadContext();
        ctx.reply("Probuild configuration reloaded.");
      })
      .command("status", ctx -> {
        var healthy = generationService.backendHealthy();
        ctx.reply("Backend: " + (healthy ? "online" : "offline"));
        ctx.reply("Placement: " + plugin.placementBackend());
        ctx.reply("WorldEdit: " + (plugin.worldEditPresent() ? "installed" : "not installed"));
        ctx.reply("Active generations: " + generationService.activeGenerations());
      })
      .build();
  }
}
