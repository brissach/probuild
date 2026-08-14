package io.brissach.probuild.util.command;

@FunctionalInterface
public interface CommandHandler {
  void handle(CommandContext ctx);
}
