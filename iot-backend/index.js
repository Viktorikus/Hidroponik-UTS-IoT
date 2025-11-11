// Import modules
const express = require("express");
const mysql = require("mysql2");
const cors = require("cors");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json()); // Penting untuk membaca req.body

// Connect to database
const db = mysql.createConnection({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  database: process.env.DB_NAME,
});

db.connect(err => {
  if (err) {
    console.log("Database connection failed:", err);
  } else {
    console.log("Database connected.");
  }
});

// === RUTE BARU UNTUK MENYIMPAN DATA (DARI MQTT.PY) ===
app.post("/api/data_sensor", (req, res) => {
  // Ambil data (suhu, humidity, lux) dari body request
  // yang dikirim oleh mqtt.py
  const { suhu, humidity, lux } = req.body;

  // Validasi sederhana
  if (suhu === undefined || humidity === undefined || lux === undefined) {
    return res.status(400).json({ error: "Data tidak lengkap. Butuh suhu, humidity, dan lux." });
  }

  // Siapkan query SQL untuk INSERT
  // Kita juga memasukkan timestamp saat ini menggunakan new Date()
  const sql = "INSERT INTO data_sensor (suhu, humidity, lux, timestamp) VALUES (?, ?, ?, ?)";
  const values = [suhu, humidity, lux, new Date()];

  // Eksekusi query
  db.query(sql, values, (err, result) => {
    if (err) {
      console.error("Database insert failed:", err);
      return res.status(500).json({ error: "Gagal menyimpan data ke database", details: err });
    }
    
    // Kirim respon sukses kembali ke mqtt.py
    console.log(`✓ Data baru disimpan ke DB. ID: ${result.insertId}`);
    res.status(200).json({ 
        message: "Data saved successfully", 
        id: result.insertId 
    });
  });
});


// === RUTE LAMA UNTUK MENGAMBIL DATA (UNTUK FRONTEND) ===
app.get("/api/data_sensor", (req, res) => {
  // Ubah LIMIT menjadi 10 agar bisa digunakan untuk grafik dan tabel
  const sql = "SELECT id, suhu, humidity, lux, timestamp FROM data_sensor ORDER BY timestamp DESC LIMIT 10";
  
  db.query(sql, (err, result) => {
    if (err) return res.status(500).json({ error: err });
    
    // Kembalikan array berisi 10 data
    res.json(result); 
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));