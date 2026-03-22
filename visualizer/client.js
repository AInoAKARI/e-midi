const canvas = document.getElementById("grid");
const statusIndicator = document.getElementById("statusIndicator");
const sourceFilter = document.getElementById("sourceFilter");
const visualizer = new window.GridVisualizer(canvas);
const knownSources = new Set(["all"]);

function updateStatus(connected) {
  statusIndicator.textContent = connected ? "🟢 connected" : "🔴 disconnected";
}

function addSourceOption(sourceId) {
  if (!sourceId || knownSources.has(sourceId)) return;
  knownSources.add(sourceId);
  const option = document.createElement("option");
  option.value = sourceId;
  option.textContent = sourceId;
  sourceFilter.appendChild(option);
}

function connect() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${proto}//${window.location.host}/ws/receive`);

  socket.addEventListener("open", () => {
    updateStatus(true);
    socket.send("viewer-ready");
  });

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.source_id) {
      addSourceOption(payload.source_id);
    }
    visualizer.receive(payload);
  });

  socket.addEventListener("close", () => {
    updateStatus(false);
    setTimeout(connect, 1000);
  });

  socket.addEventListener("error", () => {
    socket.close();
  });
}

sourceFilter.addEventListener("change", (event) => {
  visualizer.setFilter(event.target.value);
});

function loop() {
  visualizer.draw();
  window.requestAnimationFrame(loop);
}

updateStatus(false);
connect();
loop();
