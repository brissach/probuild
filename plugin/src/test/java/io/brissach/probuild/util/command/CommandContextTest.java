package io.brissach.probuild.util.command;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class CommandContextTest {

  @Test
  void joinArgsFromIndex() {
    var ctx = new CommandContext(null, null, "probuild", new String[] {
      "create", "stone", "tower"
    });
    assertEquals("stone tower", ctx.joinArgs(1));
    assertEquals("", ctx.joinArgs(4));
  }

  @Test
  void subcommand() {
    var ctx = new CommandContext(null, null, "probuild", new String[] { "reload" });
    assertEquals("reload", ctx.subcommand());
  }
}
