package io.brissach.probuild.util.command;

import java.util.List;

@FunctionalInterface
public interface TabProvider {
  List<String> complete(CommandContext ctx);
}
