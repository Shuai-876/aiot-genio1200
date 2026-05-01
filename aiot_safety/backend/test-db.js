const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
  process.env.DB_DATABASE,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    dialect: 'postgres',
  }
);

async function test() {
  try {
    await sequelize.authenticate();
    console.log('✅ Connection has been established successfully.');
    const [results] = await sequelize.query('SELECT current_database();');
    console.log('Connected to database:', results[0].current_database);
    
    const [tables] = await sequelize.query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'");
    console.log('Tables in database:', tables.map(t => t.table_name));
    
  } catch (error) {
    console.error('❌ Unable to connect to the database:', error.message);
  } finally {
    await sequelize.close();
  }
}

test();
