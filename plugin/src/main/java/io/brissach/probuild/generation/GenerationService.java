package io.brissach.probuild.generation;

import io.brissach.probuild.Context;
import io.brissach.probuild.api.ProbuildClient;
import io.brissach.probuild.structure.StructurePlacer;
import io.brissach.probuild.structure.StructureValidator;
import io.brissach.probuild.task.GenerationTask;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;

public final class GenerationService {

  private final JavaPlugin plugin;
  private final ExecutorService executor;
  private final Semaphore concurrency;
  private final AtomicInteger activeGenerations = new AtomicInteger();
  private final AtomicReference<Snapshot> snapshot;

  public GenerationService(
    JavaPlugin plugin,
    ProbuildClient client,
    StructureValidator validator,
    StructurePlacer placer,
    Context context
  ) {
    this.plugin = plugin;
    this.executor = Executors.newFixedThreadPool(Math.max(1, context.maxConcurrentGenerations()));
    this.concurrency = new Semaphore(context.maxConcurrentGenerations());
    this.snapshot = new AtomicReference<>(new Snapshot(context, client, validator, placer));
  }

  public void rebind(
    Context context,
    ProbuildClient client,
    StructureValidator validator,
    StructurePlacer placer
  ) {
    snapshot.set(new Snapshot(context, client, validator, placer));
  }

  public boolean beginGeneration(Player player, GenerationRequest request) {
    if (!concurrency.tryAcquire()) {
      player.sendMessage("Probuild is busy. Try again shortly.");
      return false;
    }
    activeGenerations.incrementAndGet();
    player.sendMessage("Probuild generation started...");
    executor.submit(new GenerationTask(
      plugin,
      snapshot.get(),
      player,
      request,
      () -> {
        activeGenerations.decrementAndGet();
        concurrency.release();
      }
    ));
    return true;
  }

  public int activeGenerations() {
    return activeGenerations.get();
  }

  public boolean backendHealthy() {
    return snapshot.get().client().isHealthy();
  }

  public void shutdown() {
    executor.shutdownNow();
  }

  public record Snapshot(
    Context context,
    ProbuildClient client,
    StructureValidator validator,
    StructurePlacer placer
  ) {}
}
