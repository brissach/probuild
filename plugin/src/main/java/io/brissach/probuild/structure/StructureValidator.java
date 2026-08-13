package io.brissach.probuild.structure;

import io.brissach.probuild.Context;
import io.brissach.probuild.util.Materials;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public final class StructureValidator {

  private final Context context;

  public StructureValidator(Context context) {
    this.context = context;
  }

  public ValidationResult validate(Structure structure) {
    var issues = new ArrayList<String>();
    if (structure.width() < 1 || structure.height() < 1 || structure.depth() < 1) {
      issues.add("invalid dimensions");
    }
    if (structure.width() > context.maxWidth()
      || structure.height() > context.maxHeight()
      || structure.depth() > context.maxDepth()) {
      issues.add("dimensions exceed plugin limits");
    }
    if (structure.blockCount() > context.maxBlocks()) {
      issues.add("block count exceeds limit");
    }
    for (var block : structure.blocks()) {
      if (block.x() < 0 || block.y() < 0 || block.z() < 0
        || block.x() >= structure.width()
        || block.y() >= structure.height()
        || block.z() >= structure.depth()) {
        issues.add("block out of bounds");
        break;
      }
      if (!Materials.isSupported(block.blockId())) {
        issues.add("unsupported block: " + block.blockId());
        break;
      }
    }
    return issues.isEmpty()
      ? ValidationResult.ok()
      : ValidationResult.failed(issues);
  }

  public record ValidationResult(boolean isValid, List<String> issues) {
    public static ValidationResult ok() {
      return new ValidationResult(true, List.of());
    }

    public static ValidationResult failed(List<String> issues) {
      return new ValidationResult(false, List.copyOf(issues));
    }

    public Optional<String> message() {
      return issues.isEmpty() ? Optional.empty() : Optional.of(String.join("; ", issues));
    }
  }
}
