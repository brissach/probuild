package io.brissach.probuild.util.command;

import java.util.Arrays;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

public record CommandContext(
  CommandSender sender,
  Command command,
  String label,
  String[] args
) {

  public void reply(String message) {
    sender.sendMessage(message);
  }

  public String subcommand() {
    return args.length > 0 ? args[0].toLowerCase() : "";
  }

  public String arg(int index) {
    return index >= 0 && index < args.length ? args[index] : "";
  }

  public String joinArgs(int from) {
    if (from >= args.length) {
      return "";
    }
    return String.join(" ", Arrays.copyOfRange(args, from, args.length));
  }

  public Player player() {
    return sender instanceof Player p ? p : null;
  }

  public Player requirePlayer() {
    var player = player();
    if (player == null) {
      throw new CommandException("Only players can run this command.");
    }
    return player;
  }

  public void requirePermission(String permission) {
    if (!sender.hasPermission(permission)) {
      throw new CommandException("Missing permission " + permission);
    }
  }

  public void requireArgs(int count, String usage) {
    if (args.length < count) {
      throw new CommandException(usage);
    }
  }
}
