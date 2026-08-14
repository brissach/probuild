package io.brissach.probuild.util.command;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;

public final class Commands implements CommandExecutor, TabCompleter {

  private final String usage;
  private final Map<String, Entry> entries;

  private Commands(String usage, Map<String, Entry> entries) {
    this.usage = usage;
    this.entries = entries;
  }

  public static Builder builder() {
    return new Builder();
  }

  @Override
  public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
    if (args.length == 0) {
      sender.sendMessage(usage);
      return true;
    }
    var entry = entries.get(args[0].toLowerCase(Locale.ROOT));
    if (entry == null) {
      sender.sendMessage("Unknown subcommand.");
      return true;
    }
    try {
      entry.handler().handle(new CommandContext(sender, command, label, args));
    } catch (CommandException ex) {
      sender.sendMessage(ex.getMessage());
    }
    return true;
  }

  @Override
  public List<String> onTabComplete(
    CommandSender sender,
    Command command,
    String alias,
    String[] args
  ) {
    if (args.length == 1) {
      var prefix = args[0].toLowerCase(Locale.ROOT);
      return entries.keySet().stream()
        .filter(name -> name.startsWith(prefix))
        .filter(name -> entries.get(name).canRun(sender))
        .sorted()
        .toList();
    }
    if (args.length > 1) {
      var entry = entries.get(args[0].toLowerCase(Locale.ROOT));
      if (entry != null && entry.tabProvider() != null && entry.canRun(sender)) {
        return entry.tabProvider().complete(new CommandContext(sender, command, alias, args));
      }
    }
    return List.of();
  }

  private record Entry(
    CommandHandler handler,
    TabProvider tabProvider,
    String permission
  ) {
    boolean canRun(CommandSender sender) {
      return permission == null || sender.hasPermission(permission);
    }
  }

  public static final class Builder {

    private String usage = "Usage: /<command> <subcommand>";
    private final Map<String, Entry> entries = new LinkedHashMap<>();

    public Builder usage(String usage) {
      this.usage = usage;
      return this;
    }

    public Builder command(String name, CommandHandler handler) {
      return command(name, null, handler);
    }

    public Builder command(String name, String permission, CommandHandler handler) {
      entries.put(name.toLowerCase(Locale.ROOT), new Entry(handler, null, permission));
      return this;
    }

    public Builder tabComplete(String name, TabProvider provider) {
      var key = name.toLowerCase(Locale.ROOT);
      var existing = entries.get(key);
      if (existing == null) {
        throw new IllegalStateException("unknown command: " + name);
      }
      entries.put(key, new Entry(existing.handler(), provider, existing.permission()));
      return this;
    }

    public Commands build() {
      return new Commands(usage, Map.copyOf(entries));
    }
  }
}
