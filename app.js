// Main application entry point
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Welcome to Travel Planner!');
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});