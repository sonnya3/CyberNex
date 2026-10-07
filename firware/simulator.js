const mqtt = require("mqtt");
const client = mqtt.connect("mqtt://localhost:5555");

function random(min, max) {
  return +(Math.random() * (max - min) + min).toFixed(2);
}

client.on("connect", () => {
  console.log("✅ Simulateur ESP8266 connecté au broker MQTT");
  setInterval(() => {
    const payload = {
      device_id: "ESP8266-SIM-01",
      timestamp: new Date().toISOString(),
      temperature: random(20, 45),
      humidity: random(30, 80),
      gaz: random(100, 600),
      presence: Math.random() > 0.8 ? 1 : 0,
    };
    client.publish("sentinelx/sensors", JSON.stringify(payload));
    console.log("[PUB]", payload);
  }, 2000);
});

client.on("error", (err) => console.error("❌ Erreur MQTT :", err.message));
