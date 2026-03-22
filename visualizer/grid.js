class GridVisualizer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.size = 50;
    this.cell = 12;
    this.trails = new Map();
    this.points = new Map();
    this.flashFrames = 0;
    this.filter = "all";
    this.sourcePalette = {
      akari: { hueShift: 320, tint: [255, 120, 190] },
      kiratan: { hueShift: 210, tint: [110, 170, 255] },
      default: { hueShift: 35, tint: [255, 210, 90] },
    };
  }

  setFilter(sourceId) {
    this.filter = sourceId;
  }

  sourceColor(sourceId, tension) {
    const palette = this.sourcePalette[sourceId] || this.sourcePalette.default;
    const baseHue = 220 - Math.round((tension / 127) * 220);
    const hue = sourceId === "akari" || sourceId === "kiratan"
      ? palette.hueShift
      : baseHue;
    return `hsl(${hue}, 85%, 60%)`;
  }

  receive(message) {
    if (message.type === "bounce") {
      if (this.filter === "all" || this.filter === message.source_id) {
        this.flashFrames = 1;
      }
      return;
    }

    if (message.type !== "emotion") return;
    if (this.filter !== "all" && message.source_id !== this.filter) return;

    const x = Math.max(0, Math.min(49, Math.floor((message.valence / 127) * 49)));
    const y = Math.max(0, Math.min(49, Math.floor((message.arousal / 127) * 49)));
    const key = `${message.source_id}:${x}:${y}`;

    this.points.set(message.source_id, {
      x,
      y,
      tension: message.tension,
      source_id: message.source_id,
      brightness: 255,
      bounce: message.bounce,
    });
    this.trails.set(key, {
      x,
      y,
      tension: message.tension,
      source_id: message.source_id,
      brightness: 255,
    });
    if (message.bounce) {
      this.flashFrames = 1;
    }
  }

  decay() {
    for (const [key, cell] of this.trails.entries()) {
      cell.brightness *= 0.92;
      if (cell.brightness < 4) {
        this.trails.delete(key);
      }
    }
  }

  drawCell(x, y, color, alpha) {
    this.ctx.fillStyle = color;
    this.ctx.globalAlpha = alpha;
    this.ctx.fillRect(x * this.cell, y * this.cell, this.cell - 1, this.cell - 1);
    this.ctx.globalAlpha = 1;
  }

  draw() {
    this.decay();
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.fillStyle = "rgba(7, 17, 29, 0.95)";
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    this.ctx.strokeStyle = "rgba(55, 82, 124, 0.18)";
    for (let i = 0; i <= this.size; i += 1) {
      const p = i * this.cell;
      this.ctx.beginPath();
      this.ctx.moveTo(p, 0);
      this.ctx.lineTo(p, this.canvas.height);
      this.ctx.stroke();
      this.ctx.beginPath();
      this.ctx.moveTo(0, p);
      this.ctx.lineTo(this.canvas.width, p);
      this.ctx.stroke();
    }

    for (const cell of this.trails.values()) {
      const alpha = Math.min(1, cell.brightness / 255);
      this.drawCell(cell.x, cell.y, this.sourceColor(cell.source_id, cell.tension), alpha);
    }

    for (const point of this.points.values()) {
      const color = this.sourceColor(point.source_id, point.tension);
      this.drawCell(point.x, point.y, color, 1);
      this.ctx.fillStyle = "rgba(255,255,255,0.9)";
      this.ctx.beginPath();
      this.ctx.arc(point.x * this.cell + 5.5, point.y * this.cell + 5.5, 3, 0, Math.PI * 2);
      this.ctx.fill();
    }

    if (this.flashFrames > 0) {
      this.ctx.fillStyle = "rgba(255,255,255,0.92)";
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      this.flashFrames -= 1;
    }
  }
}

window.GridVisualizer = GridVisualizer;
