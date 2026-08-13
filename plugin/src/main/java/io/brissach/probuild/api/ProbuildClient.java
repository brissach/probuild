package io.brissach.probuild.api;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import io.brissach.probuild.Context;
import io.brissach.probuild.security.RequestSigner;
import io.brissach.probuild.serialization.StructureCodec;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;

public final class ProbuildClient {

  private static final Gson GSON = new Gson();

  private final Context context;
  private final RequestSigner signer;
  private final HttpClient httpClient;
  private final StructureCodec codec;

  public ProbuildClient(Context context, RequestSigner signer) {
    this.context = context;
    this.signer = signer;
    this.codec = new StructureCodec();
    this.httpClient = HttpClient.newBuilder()
      .connectTimeout(Duration.ofMillis(context.timeoutMs()))
      .build();
  }

  public ApiResponse generate(ApiRequest request) throws IOException, InterruptedException {
    var payload = new JsonObject();
    payload.addProperty("prompt", request.prompt());
    payload.addProperty("seed", request.seed());
    payload.addProperty("width", request.width());
    payload.addProperty("height", request.height());
    payload.addProperty("depth", request.depth());
    payload.addProperty("temperature", request.temperature());
    payload.addProperty("top_k", request.topK());
    payload.addProperty("top_p", 1.0);

    var body = GSON.toJson(payload).getBytes(StandardCharsets.UTF_8);
    var timestamp = String.valueOf(System.currentTimeMillis() / 1000L);
    var requestId = UUID.randomUUID().toString().replace("-", "");
    var signature = signer.sign(timestamp, requestId, body);

    var httpRequest = HttpRequest.newBuilder()
      .uri(URI.create(context.backendUrl() + "/v1/generation"))
      .timeout(Duration.ofMillis(context.timeoutMs()))
      .header("Content-Type", "application/json")
      .header("Authorization", "Bearer " + context.apiKey())
      .header("X-ProBuild-Timestamp", timestamp)
      .header("X-ProBuild-Request-Id", requestId)
      .header("X-ProBuild-Signature", signature)
      .POST(HttpRequest.BodyPublishers.ofByteArray(body))
      .build();

    var response = httpClient.send(httpRequest, HttpResponse.BodyHandlers.ofString());
    if (response.statusCode() >= 400) {
      throw new IOException("backend returned " + response.statusCode() + ": " + response.body());
    }

    var json = GSON.fromJson(response.body(), JsonObject.class);
    var structure = codec.decode(json.getAsJsonObject("structure"));
    var metadata = json.getAsJsonObject("metadata");
    return new ApiResponse(
      json.get("generation_id").getAsString(),
      structure,
      metadata.get("duration_ms").getAsLong()
    );
  }

  public boolean isHealthy() {
    try {
      var request = HttpRequest.newBuilder()
        .uri(URI.create(context.backendUrl() + "/v1/health"))
        .timeout(Duration.ofMillis(context.timeoutMs()))
        .GET()
        .build();
      var response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      return response.statusCode() == 200;
    } catch (Exception ex) {
      return false;
    }
  }
}
