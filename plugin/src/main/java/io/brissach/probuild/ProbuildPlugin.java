package io.brissach.probuild;

import io.brissach.probuild.api.ProbuildClient;
import io.brissach.probuild.command.ProbuildCommand;
import io.brissach.probuild.generation.GenerationService;
import io.brissach.probuild.security.RequestSigner;
import io.brissach.probuild.structure.StructurePlacer;
import io.brissach.probuild.structure.StructureValidator;
import io.brissach.probuild.world.WorldEditSupport;
import org.bukkit.plugin.java.JavaPlugin;

public final class ProbuildPlugin extends JavaPlugin {

  private Context context;
  private GenerationService generationService;
  private StructurePlacer structurePlacer;

  @Override
  public void onEnable() {
    saveDefaultConfig();
    context = Context.from(getConfig());
    var signer = new RequestSigner(context.signingSecret());
    var client = new ProbuildClient(context, signer);
    var validator = new StructureValidator(context);
    structurePlacer = new StructurePlacer(
      WorldEditSupport.resolve(this, context.placementBackend()),
      validator
    );
    generationService = new GenerationService(this, client, validator, structurePlacer, context);
    var command = getCommand("probuild");
    if (command != null) {
      var executor = ProbuildCommand.create(this, generationService, context);
      command.setExecutor(executor);
      command.setTabCompleter(executor);
    }
    getLogger().info("Probuild enabled (placement=" + structurePlacer.world().id() + ")");
  }

  @Override
  public void onDisable() {
    if (generationService != null) {
      generationService.shutdown();
    }
  }

  public void reloadContext() {
    reloadConfig();
    context = Context.from(getConfig());
    var signer = new RequestSigner(context.signingSecret());
    var client = new ProbuildClient(context, signer);
    var validator = new StructureValidator(context);
    structurePlacer = new StructurePlacer(
      WorldEditSupport.resolve(this, context.placementBackend()),
      validator
    );
    generationService.rebind(context, client, validator, structurePlacer);
  }

  public Context context() {
    return context;
  }

  public String placementBackend() {
    return structurePlacer.world().id();
  }

  public boolean worldEditPresent() {
    return WorldEditSupport.isPresent();
  }
}
