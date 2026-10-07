const express = require("express");
const mqtt = require("mqtt");
const WebSocket = require("ws");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const server = app.listen(3000, () => console.log("API sur :3000"));
const wss = new WebSocket.Server({ server });

const mqttClient = mqtt.connect("mqtt://mosquitto:1883");
const alerts = [];

mqttClient.on("connect", () => {
  console.log("API connectée au broker MQTT");
  mqttClient.subscribe("sentinelx/sensors");
});

mqttClient.on("message", (topic, message) => {
  const data = JSON.parse(message.toString());
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(data));
    }
  });
  if (data.temperature > 40 || data.gaz > 500 || data.presence === 1) {
    alerts.push({ ...data, type: "ALERT" });
  }
});

app.get("/api/v1/alerts", (req, res) => res.json(alerts));
app.post("/api/v1/alerts", (req, res) => {
  alerts.push(req.body);
  res.status(201).json({ status: "ok" });
});
app.get("/api/v1/health", (req, res) => res.json({ status: "up" }));
