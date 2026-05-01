const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

// 偵測紀錄 Table
const Detection = sequelize.define('Detection', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  className: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  confidence: {
    type: DataTypes.FLOAT,
    allowNull: false,
  },
  timestamp: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  deviceId: {
    type: DataTypes.STRING,
    allowNull: false,
  },
}, { timestamps: false });

// 審計報告 Table
const SafetyAudit = sequelize.define('SafetyAudit', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  reportContent: {
    type: DataTypes.TEXT,
    allowNull: false,
  },
  violationCount: {
    type: DataTypes.INTEGER,
    allowNull: false,
  },
}, {
  timestamps: true,
  updatedAt: false,
});

// 每秒聚合偵測統計（供 Grafana 時序圖使用）
const DetectionStat = sequelize.define('DetectionStat', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  時間: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  label0: { type: DataTypes.INTEGER, defaultValue: 0 },
  label1: { type: DataTypes.INTEGER, defaultValue: 0 },
  label2: { type: DataTypes.INTEGER, defaultValue: 0 },
  label3: { type: DataTypes.INTEGER, defaultValue: 0 },
  label4: { type: DataTypes.INTEGER, defaultValue: 0 },
  label5: { type: DataTypes.INTEGER, defaultValue: 0 },
}, { timestamps: false });

// One-to-Many：一份審計報告 對應 多筆偵測紀錄
SafetyAudit.hasMany(Detection);
Detection.belongsTo(SafetyAudit);

module.exports = { Detection, DetectionStat, SafetyAudit, sequelize };
