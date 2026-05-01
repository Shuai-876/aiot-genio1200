const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
const express = require('express');
const cors = require('cors');
const { DetectionStat, sequelize } = require('./models');

const app = express();
app.use(cors());
app.use(express.json());

// POST /api/detections
// 接收 main.py 每秒送來的 summary，寫入 DetectionStat
app.post('/api/detections', async (req, res) => {
  try {
    const { summary, timestamp } = req.body;
    const ts = new Date(timestamp);

    const row = {
      時間: ts,
      label0: summary[0] || 0,
      label1: summary[1] || 0,
      label2: summary[2] || 0,
      label3: summary[3] || 0,
      label4: summary[4] || 0,
      label5: summary[5] || 0,
    };

    await DetectionStat.create(row);
    console.log(`[DB] ${ts.toLocaleTimeString()} | label0:${row.label0} label1:${row.label1} label2:${row.label2} label3:${row.label3} label4:${row.label4} label5:${row.label5}`);
    res.status(200).send();
  } catch (err) {
    console.error('saveDetection error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// GET /api/detections?limit=100
app.get('/api/detections', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 100;
    const rows = await DetectionStat.findAll({
      order: [['時間', 'DESC']],
      limit,
      raw: true,
    });
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 健康檢查
app.get('/health', (req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3001;

sequelize
  .sync({ alter: true })
  .then(() => {
    console.log('✅ 資料庫已連接並同步 Schema');
    app.listen(PORT, () =>
      console.log(`🚀 API Server 運行於 http://localhost:${PORT}`)
    );
  })
  .catch((err) => {
    console.error('❌ 資料庫連接失敗:', err.message);
    process.exit(1);
  });
