from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import random
import re
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure GitHub Models API
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.getenv("GITHUB_TOKEN"),
)

app = Flask(__name__)
CORS(app)

# Global data storage
FIELDS = []  # Empty list to start
WATER_TANK = 5000      # Current water level
TANK_CAPACITY = 5000   # Total tank capacity
NEXT_FIELD_ID = 1  # Auto-increment field ID

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Irrigation Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 20px 0;
        }
        
        .header h1 {
            font-size: 3em;
            font-weight: 800;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            background: linear-gradient(90deg, #ffffff 0%, #bae6fd 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.85;
            font-weight: 400;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.5;
            color: #bae6fd;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            display: none;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.success {
            background-color: rgba(46, 213, 115, 0.9);
            color: white;
        }
        
        .message.error {
            background-color: rgba(255, 71, 87, 0.9);
            color: white;
        }
        
        .message.info {
            background-color: rgba(102, 126, 234, 0.9);
            color: white;
        }
        
        .message.critical {
            background-color: rgba(255, 71, 87, 0.95);
            color: white;
            font-size: 1.1em;
            border-left: 5px solid white;
        }
        
        .message.show {
            display: block;
        }
        
        /* Water Tank Section */
        .water-tank-section {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .water-tank-card {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .water-tank-card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.4em;
        }
        
        .water-status {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }
        
        .water-bar {
            background-color: #e0e0e0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .water-fill {
            background: linear-gradient(90deg, #0ea5e9 0%, #06b6d4 100%);
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .water-info {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }
        
        .refill-form {
            display: flex;
            gap: 10px;
        }
        
        .refill-form input {
            flex: 1;
            padding: 10px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .refill-form button {
            padding: 10px 20px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .refill-form button:hover {
            background-color: #764ba2;
            transform: translateY(-2px);
        }
        
        /* Add Field Form */
        .form-section {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .form-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        
        .form-group-with-button {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }
        
        .form-group-with-button input {
            flex: 1;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border 0.3s ease;
        }
        
        .form-group-with-button input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .lookup-btn {
            padding: 10px 15px;
            background-color: #764ba2;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 0.9em;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        
        .lookup-btn:hover {
            background-color: #667eea;
            transform: translateY(-2px);
        }
        
        .lookup-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .form-group input {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-buttons {
            display: flex;
            gap: 10px;
        }
        
        .btn-primary {
            padding: 12px 24px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            background-color: #764ba2;
            transform: translateY(-2px);
        }
        
        /* Control Buttons */
        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn-secondary {
            background-color: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 12px 24px;
            font-size: 1em;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn-secondary:hover {
            background-color: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        /* AI Plan Container */
        #aiPlanContainer {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            display: none;
            animation: fadeIn 0.5s ease;
        }
        
        #aiPlanContainer.show {
            display: block;
        }
        
        .ai-plan-header {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
        }
        
        .ai-plan-header h2 {
            font-size: 1.6em;
            margin-bottom: 10px;
        }
        
        .ai-plan-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .ai-stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .ai-stat-label {
            font-size: 0.85em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .ai-stat-value {
            font-size: 1.8em;
            font-weight: bold;
        }
        
        .ai-strategy {
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
        }
        
        .ai-strategy strong {
            color: #667eea;
        }
        
        .field-allocations {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }
        
        .allocation-card {
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
        }
        
        .allocation-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        .allocation-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .allocation-status-icon {
            font-size: 1.5em;
        }
        
        .allocation-status-icon.allocated {
            color: #2ed573;
        }
        
        .allocation-status-icon.skipped {
            color: #ff4757;
        }
        
        .allocation-field-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
            flex: 1;
        }
        
        .allocation-liters {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .allocation-reason {
            color: #666;
            font-size: 0.9em;
            line-height: 1.4;
        }
        
        /* Field Cards */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
        
        .field-card {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 20px;
            color: #1e293b;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
        }
        
        .field-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.25);
        }
        
        .field-card.critical {
            background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
        }
        
        .field-card.high {
            background: linear-gradient(135deg, #ffa502 0%, #ff8500 100%);
        }
        
        .field-card.medium {
            background: linear-gradient(135deg, #ffd602 0%, #ffb300 100%);
        }
        
        .field-card.low {
            background: linear-gradient(135deg, #2ed573 0%, #26b873 100%);
        }
        
        .field-card-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        
        .field-card h3 {
            font-size: 1.3em;
            margin-bottom: 5px;
        }
        
        .field-card p {
            font-size: 0.85em;
            margin-bottom: 8px;
            opacity: 0.95;
        }
        
        .delete-btn {
            background-color: rgba(255, 255, 255, 0.3);
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            transition: background-color 0.3s ease;
        }
        
        .delete-btn:hover {
            background-color: rgba(255, 255, 255, 0.5);
        }
        
.priority-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 10px;
        }

        .field-card.critical { border-left: 5px solid #ff4757; }
        .field-card.high     { border-left: 5px solid #ffa502; }
        .field-card.medium   { border-left: 5px solid #ffd602; }
        .field-card.low      { border-left: 5px solid #2ed573; }

        .field-card.critical .priority-badge { background: #ff4757; color: white; }
        .field-card.high     .priority-badge { background: #ffa502; color: white; }
        .field-card.medium   .priority-badge { background: #ffd602; color: #333; }
        .field-card.low      .priority-badge { background: #2ed573; color: white; }
        
        .moisture-info {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.3);
        }
        
.moisture-bar {
            background-color: #e0e0e0;
            height: 8px;
            border-radius: 5px;
            overflow: hidden;
            margin: 8px 0;
        }
        
        .moisture-fill {
            background: linear-gradient(90deg, #0ea5e9 0%, #06b6d4 100%);
            height: 100%;
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        .water-needed {
            margin-top: 12px;
            padding: 10px;
            background-color: #f0f9ff;
            border-radius: 6px;
            font-weight: bold;
            color: #0369a1;
        }
        
        .card-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .toggle-water-btn {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 0.9em;
            transition: all 0.3s ease;
            color: white;
        }
        
        .toggle-water-btn.off {
            background-color: rgba(255, 255, 255, 0.4);
        }
        
        .toggle-water-btn.on {
            background-color: #2ed573;
        }
        
        .toggle-water-btn:hover {
            transform: scale(1.05);
        }
        
        .empty-state {
            color: white;
            text-align: center;
            padding: 40px;
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💧 Farm Water Agent</h1>
            <p>Thirsty vs. Can Wait — AI That Rations Water Before It Runs Out</p>
        </div>
        
        <div id="message" class="message"></div>
        
        <!-- Water Tank Section -->
        <div class="water-tank-section">
            <div class="water-tank-card">
                <h2>💧 Water Tank Status</h2>
                <div class="water-status" id="waterStatus">5000 / 5000 L</div>
                <div class="water-bar">
                    <div class="water-fill" id="waterFill" style="width: 100%"></div>
                </div>
                <div class="water-info">Tank Capacity: 5000 liters</div>
            </div>
            
            <div class="water-tank-card">
                <h2>🔄 Refill Tank</h2>
                <form class="refill-form" onsubmit="refillTank(event)">
                    <input type="number" id="refillAmount" placeholder="Enter amount (liters)" min="1" step="10" required>
                    <button type="submit" class="btn-primary">Refill</button>
                </form>
            </div>

            <div class="water-tank-card">
                <h2>⚙️ Set Capacity</h2>
                <form class="refill-form" onsubmit="setTankCapacity(event)">
                    <input type="number" id="tankCapacity" placeholder="Enter capacity (liters)" min="1" step="10" required>
                    <button type="submit" class="btn-primary">Set</button>
                    </form>
            </div>

        </div>
        
        <!-- Add Field Form -->
        <div class="form-section">
            <h2>➕ Add New Field</h2>
            <form onsubmit="addField(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="fieldName">Field Name</label>
                        <input type="text" id="fieldName" required>
                    </div>
                    <div class="form-group">
                        <label for="treeType">Tree Type</label>
                        <input type="text" id="treeType" required>
                    </div>
                    <div class="form-group">
                        <label for="treeCount">Tree Count</label>
                        <input type="number" id="treeCount" min="1" required>
                    </div>
                    <div class="form-group">
                        <label for="position">Position</label>
                        <input type="text" id="position" placeholder="e.g., North, South" required>
                    </div>
                    <div class="form-group">
                        <label for="area">Area (m²)</label>
                        <input type="number" id="area" min="1" step="0.1" required>
                    </div>
                    <div class="form-group">
                        <label for="currentMoisture">Current Moisture %</label>
                        <input type="number" id="currentMoisture" min="0" max="100" step="0.1" required>
                    </div>
                    <div class="form-group">
                        <label>Target Moisture %</label>
                        <div class="form-group-with-button">
                            <input type="number" id="targetMoisture" min="0" max="100" step="0.1" required>
                            <button type="button" class="lookup-btn" onclick="lookupTreeWaterNeeds()">🔍 Lookup</button>
                        </div>
                    </div>
                </div>
                <div class="form-buttons">
                    <button type="submit" class="btn-primary">Add Field</button>
                </div>
            </form>
        </div>
        
        <!-- Control Buttons -->
        <div class="controls">
            <button onclick="simulateSensorData()" class="btn-secondary">Simulate Sensor Data</button>
            <button onclick="runWaterDistribution()" class="btn-secondary">Run Water Distribution</button>
            <button onclick="generateRationingPlan()" class="btn-secondary">🤖 AI Rationing Plan</button>
            <button onclick="resetDemo()" class="btn-secondary">Reset Demo</button>
        </div>
        
        <!-- AI Rationing Plan Container -->
        <div id="aiPlanContainer"></div>
        
        <!-- Field Cards -->
        <div class="cards-grid" id="fieldsContainer">
            <div class="empty-state">No fields yet. Add a field to get started!</div>
        </div>
    </div>
    
    <script>
        // Calculate water needed for a field
        function calculateWaterNeeded(field) {
            return Math.round(Math.abs(field.target_moisture - field.current_moisture) * field.area_m2 * 0.01 * 100) / 100;
        }
        
        // Calculate priority for a field
        function calculatePriority(field) {
            const current = field.current_moisture;
            const target = field.target_moisture;
            
            if (current < 30) return "critical";
            if (current < target - 10) return "high";
            if (current < target) return "medium";
            return "low";
        }
        
        // Set tank capacity handler

        async function setTankCapacity(event) {
            event.preventDefault();
            const capacity = parseFloat(document.getElementById('tankCapacity').value);
            try {
                const response = await fetch('/api/tank-capacity', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ capacity: capacity })
                });
                if (!response.ok) throw new Error('Failed');
                const data = await response.json();
                showMessage(`Tank capacity set to ${capacity} L`, 'success');
                updateWaterTankDisplay(data);
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
            }   
        }

        // Lookup optimal water needs for tree type using AI
        async function lookupTreeWaterNeeds() {
            const treeType = document.getElementById('treeType').value.trim();
            
            if (!treeType) {
                alert('Please enter a tree type first');
                return;
            }
            
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ Loading...';
            
            try {
                const response = await fetch('/api/tree-knowledge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tree_type: treeType })
                });
                
                const data = await response.json();
                
                if (data.optimal_moisture) {
                    document.getElementById('targetMoisture').value = data.optimal_moisture;
                    showMessage(`✅ Optimal moisture for ${treeType}: ${data.optimal_moisture}%`, 'success');
                } else {
                    alert('Using default 60%');
                    document.getElementById('targetMoisture').value = 60;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Using default 60%');
                document.getElementById('targetMoisture').value = 60;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Lookup';
            }
        }
        
        // Load and display fields
        async function loadFields() {
            try {
                const response = await fetch('/api/distribute');
                if (!response.ok) throw new Error('Failed to load fields');
                const fields = await response.json();
                displayFields(fields);
                loadWaterTank();
            } catch (error) {
                console.error('Error loading fields:', error);
            }
        }
        
        // Load water tank status
        async function loadWaterTank() {
            try {
                const response = await fetch('/api/water-tank');
                if (!response.ok) throw new Error('Failed to load water tank');
                const data = await response.json();
                updateWaterTankDisplay(data);
            } catch (error) {
                console.error('Error loading water tank:', error);
            }
        }
        
        // Update water tank display
        function updateWaterTankDisplay(data) {
            const percent = (data.remaining / data.total) * 100;
            document.getElementById('waterStatus').textContent = `${data.remaining} / ${data.total} L`;
            document.getElementById('waterFill').style.width = percent + '%';
        }
        
        // Display field cards
        function displayFields(fields) {
            const container = document.getElementById('fieldsContainer');
            
            if (fields.length === 0) {
                container.innerHTML = '<div class="empty-state">No fields yet. Add a field to get started!</div>';
                return;
            }
            
            container.innerHTML = '';
            
            fields.forEach(field => {
                const priority = calculatePriority(field);
                const waterNeeded = field.water_needed_liters;
                const moisturePercent = Math.round((field.current_moisture / field.target_moisture) * 100);
                
                const card = document.createElement('div');
                card.className = `field-card ${priority}`;
                
                const waterStatus = field.watering_active ? 'ON' : 'OFF';
                const waterButtonClass = field.watering_active ? 'on' : 'off';
                
                card.innerHTML = `
                    <div class="field-card-header">
                        <div>
                            <h3>${field.name}</h3>
                            <p><strong>ID:</strong> ${field.id}</p>
                        </div>
                        <button class="delete-btn" onclick="deleteField(${field.id})">Delete</button>
                    </div>
                    
                    <p><strong>Tree Type:</strong> ${field.tree_type}</p>
                    <p><strong>Tree Count:</strong> ${field.tree_count}</p>
                    <p><strong>Position:</strong> ${field.position}</p>
                    <p><strong>Area:</strong> ${field.area_m2} m²</p>
                    
                    <div class="moisture-info">
                        <p><strong>Current Moisture:</strong> ${field.current_moisture}%</p>
                        <p><strong>Target Moisture:</strong> ${field.target_moisture}%</p>
                        <div class="moisture-bar">
                            <div class="moisture-fill" style="width: ${moisturePercent}%"></div>
                        </div>
                        
                        <div class="water-needed">
                            💧 Water Needed: ${waterNeeded} L
                        </div>
                    </div>
                    
                    <span class="priority-badge">${priority}</span>
                    
                    <div class="card-actions">
                        <button class="toggle-water-btn ${waterButtonClass}" onclick="toggleWater(${field.id})">
                            Water: ${waterStatus}
                        </button>
                    </div>
                `;
                
                container.appendChild(card);
            });
        }
        
        // Add new field
        async function addField(event) {
            event.preventDefault();
            
            const fieldData = {
                name: document.getElementById('fieldName').value,
                tree_type: document.getElementById('treeType').value,
                tree_count: parseInt(document.getElementById('treeCount').value),
                position: document.getElementById('position').value,
                area_m2: parseFloat(document.getElementById('area').value),
                current_moisture: parseFloat(document.getElementById('currentMoisture').value),
                target_moisture: parseFloat(document.getElementById('targetMoisture').value)
            };
            
            try {
                const response = await fetch('/api/fields', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(fieldData)
                });
                
                if (!response.ok) throw new Error('Failed to add field');
                
                showMessage('Field added successfully!', 'success');
                event.target.reset();
                await loadFields();
            } catch (error) {
                showMessage('Error adding field: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Delete field
        async function deleteField(fieldId) {
            if (!confirm('Are you sure you want to delete this field?')) return;
            
            try {
                const response = await fetch(`/api/fields/${fieldId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) throw new Error('Failed to delete field');
                
                showMessage('Field deleted successfully!', 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error deleting field: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Toggle watering for a field
        async function toggleWater(fieldId) {
            try {
                const response = await fetch(`/api/fields/${fieldId}/water/toggle`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (response.status === 400) {
                    showMessage('Error: ' + data.error, 'error');
                    return;
                }
                
                if (data.status === 'on') {
                    showMessage(`✅ Watering ON - Used ${data.water_used} L, moisture increased by ${data.moisture_increase}%`, 'success');
                } else if (data.status === 'off') {
                    showMessage(`🛑 Watering OFF - Moisture decreased`, 'success');
                }
                
                await loadFields();
            } catch (error) {
                showMessage('Error toggling water: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Refill water tank
        async function refillTank(event) {
            event.preventDefault();
            
            const amount = parseFloat(document.getElementById('refillAmount').value);
            
            try {
                const response = await fetch('/api/water-tank/refill', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount: amount })
                });
                
                if (!response.ok) throw new Error('Failed to refill tank');
                const data = await response.json();
                
                showMessage(`Tank refilled with ${amount} L! Remaining: ${data.remaining} L`, 'success');
                document.getElementById('refillAmount').value = '';
                await loadWaterTank();
            } catch (error) {
                showMessage('Error refilling tank: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Simulate sensor data with realistic drift
        async function simulateSensorData() {
            try {
                const response = await fetch('/api/simulate', {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error('Simulation failed');
                const data = await response.json();
                
                showMessage(`📊 Sensor simulation: ${data.summary}`, 'info');
                await loadFields();
            } catch (error) {
                showMessage('Error simulating data: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Run water distribution analysis
        async function runWaterDistribution() {
            try {
                const response = await fetch('/api/distribute');
                if (!response.ok) throw new Error('Failed to load distribution data');
                const fields = await response.json();
                
                // Find critical, high, and check if all low
                const criticalFields = fields.filter(f => f.priority === 'critical');
                const highFields = fields.filter(f => f.priority === 'high');
                const allLow = fields.every(f => f.priority === 'low' || f.priority === 'medium');
                
                // Show appropriate banner
                if (criticalFields.length > 0) {
                    const criticalList = criticalFields.map(f => `${f.name} (${f.water_needed_liters}L)`).join(', ');
                    showMessage(`🚨 CRITICAL: Water ${criticalList} immediately!`, 'critical');
                } else if (highFields.length > 0) {
                    const highList = highFields.map(f => f.name).join(', ');
                    showMessage(`⚠️ HIGH PRIORITY: ${highList} need watering soon`, 'info');
                } else {
                    showMessage('✅ All fields adequately watered!', 'success');
                }
                
                // Display fields with fade-in animation
                displayFields(fields);
                await loadWaterTank();
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Generate AI rationing plan
        async function generateRationingPlan() {
            const container = document.getElementById('aiPlanContainer');
            
            try {
                const response = await fetch('/api/ai-rationing');
                if (!response.ok) throw new Error('Failed to fetch rationing plan');
                
                const plan = await response.json();
                
                // Build HTML for the plan
                let html = `
                    <div class="ai-plan-header">
                        <h2>🤖 AI Water Rationing Plan</h2>
                    </div>
                    
                    <div class="ai-plan-stats">
                        <div class="ai-stat">
                            <div class="ai-stat-label">Water Available</div>
                            <div class="ai-stat-value">${plan.total_water_available} L</div>
                        </div>
                        <div class="ai-stat">
                            <div class="ai-stat-label">Water Needed</div>
                            <div class="ai-stat-value">${plan.total_water_needed} L</div>
                        </div>
                    </div>
                    
                    <div class="ai-strategy">
                        <strong>Strategy:</strong> ${plan.rationing_strategy}
                    </div>
                    
                    <h3 style="color: #667eea; margin-bottom: 15px;">Field Allocations</h3>
                    <div class="field-allocations">
                `;
                
                // Render field allocations
                if (plan.field_allocations && Array.isArray(plan.field_allocations)) {
                    plan.field_allocations.forEach(allocation => {
                        const isAllocated = allocation.allocated_liters > 0;
                        const icon = isAllocated ? '✅' : '❌';
                        const statusClass = isAllocated ? 'allocated' : 'skipped';
                        
                        html += `
                            <div class="allocation-card">
                                <div class="allocation-header">
                                    <span class="allocation-status-icon ${statusClass}">${icon}</span>
                                    <div class="allocation-field-name">${allocation.field_name}</div>
                                    <div class="allocation-liters">${allocation.allocated_liters}L</div>
                                </div>
                                <div class="allocation-reason">${allocation.reason}</div>
                            </div>
                        `;
                    });
                }
                
                html += `
                    </div>
                `;
                
                container.innerHTML = html;
                container.classList.add('show');
                
                showMessage('✅ AI rationing plan generated!', 'success');
            } catch (error) {
                showMessage('Error generating rationing plan: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Reset demo to initial state
        async function resetDemo() {
            if (!confirm('Reset all fields and water tank to initial state?')) return;
            
            try {
                const response = await fetch('/api/reset-demo', {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error('Failed to reset demo');
                const data = await response.json();
                
                // Hide AI plan container
                document.getElementById('aiPlanContainer').classList.remove('show');
                
                showMessage(data.message, 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error resetting demo: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Show message with type (success, error, info, critical)
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = `message ${type} show`;
            
            // Clear message after 5 seconds (longer for critical)
            const duration = type === 'critical' ? 6000 : 5000;
            setTimeout(() => {
                messageDiv.classList.remove('show');
            }, duration);
        }
        
        // Load fields on page load
        window.addEventListener('load', loadFields);
    </script>
</body>
</html>
"""


def calculate_priority(field):
    """
    Calculate irrigation priority based on current moisture level.
    
    Priority levels:
    - low: current_moisture >= target_moisture (enough water, no action needed)
    - critical: current_moisture < 30 (very dry, urgent)
    - high: current_moisture < target_moisture - 10 (dry, needs watering)
    - medium: current_moisture < target_moisture (slightly below target)
    """
    current = field["current_moisture"]
    target = field["target_moisture"]
    
    # If current is above or equal to target, field has enough water
    if current >= target:
        return "low"
    
    # Now we know current < target, so check severity levels
    if current < 30:
        return "critical"
    elif current < target - 10:
        return "high"
    else:
        # current < target but >= 30 and not < target - 10
        return "medium"


def calculate_water_needed(field):
    """
    Calculate water needed for a field in liters.
    
    Uses max(0, target - current) so fields at or above target show 0L needed.
    Formula: max(0, target - current) * area_m2 * 0.01
    """
    water_deficit = max(0, field["target_moisture"] - field["current_moisture"])
    return round(water_deficit * field["area_m2"] * 0.01, 2)


def get_tree_water_needs(tree_type):
    """
    Use Gemini AI to get optimal soil moisture percentage for a tree type.
    Uses the new google-genai package with improved response parsing.
    
    Args:
        tree_type (str): Name of the tree type (e.g., "Orange", "Apple")
    
    Returns:
        int: Optimal soil moisture percentage (0-100), defaults to 60 if API fails
    """
    try:
        # Create prompt for Gemini
        prompt = f"What is the optimal soil moisture percentage for growing {tree_type} trees? Respond with ONLY a number between 0 and 100 representing the percentage. No explanation."
        
        # Call GitHub Models API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        
        # Use regex to safely extract the first number from anywhere in the response
        # This is more robust than string splitting and filtering
        match = re.search(r'\d+', response_text)
        
        if match:
            optimal_moisture = int(match.group())
            
            # Ensure it's within valid range (0-100)
            if 0 <= optimal_moisture <= 100:
                return optimal_moisture
        
        # If regex didn't find a valid number, return default
        return 60
    
    except Exception as e:
        # Log the error and return default value (graceful fallback)
        print(f"Error calling Gemini API: {e}")
        return 60  # Default fallback value


@app.route("/", methods=["GET"])
def home():
    """Render the HTML dashboard."""
    return render_template_string(DASHBOARD_HTML)


# ============ Field Management Routes ============

@app.route("/api/fields", methods=["GET"])
def get_all_fields():
    """Return all fields as JSON."""
    return jsonify(FIELDS)


@app.route("/api/fields", methods=["POST"])
def create_field():
    """
    Create a new field with auto-assigned ID.
    Expected JSON: {name, tree_type, tree_count, position, area_m2, current_moisture, target_moisture}
    Stores original_current_moisture for demo reset functionality.
    """
    global NEXT_FIELD_ID
    
    data = request.get_json()
    
    # Create field with auto-assigned id
    new_field = {
        "id": NEXT_FIELD_ID,
        "name": data.get("name"),
        "tree_type": data.get("tree_type"),
        "tree_count": data.get("tree_count"),
        "position": data.get("position"),
        "area_m2": data.get("area_m2"),
        "current_moisture": data.get("current_moisture"),
        "original_current_moisture": data.get("current_moisture"),  # Store original for reset
        "target_moisture": data.get("target_moisture"),
        "watering_active": False  # Default to not watering
    }
    
    FIELDS.append(new_field)
    NEXT_FIELD_ID += 1
    
    return jsonify(new_field), 201


@app.route("/api/fields/<int:field_id>", methods=["GET"])
def get_field(field_id):
    """Return a specific field by ID."""
    for field in FIELDS:
        if field["id"] == field_id:
            return jsonify(field)
    
    return jsonify({"error": "Field not found"}), 404


@app.route("/api/fields/<int:field_id>", methods=["DELETE"])
def delete_field(field_id):
    """Delete a field by id. Deactivate watering if active."""
    global WATER_TANK
    
    for i, field in enumerate(FIELDS):
        if field["id"] == field_id:
            # If watering is active, just deactivate it (water is NOT returned)
            if field["watering_active"]:
                field["watering_active"] = False
            
            FIELDS.pop(i)
            return jsonify({"status": "deleted"}), 200
    
    return jsonify({"error": "Field not found"}), 404


@app.route("/api/fields/<int:field_id>/water/toggle", methods=["POST"])
def toggle_water(field_id):
    """
    Toggle watering for a field.
    
    When turning ON:
    - Deduct from tank (water needed = target - current adjusted)
    - Increase current_moisture by min(20, target - current)
    
    When turning OFF:
    - Just deactivate (water NOT returned to tank - simulates consumption)
    """
    global WATER_TANK
    
    for field in FIELDS:
        if field["id"] == field_id:
            water_needed = calculate_water_needed(field)
            
            if not field["watering_active"]:
                # Turning ON: check if enough water, deduct, and increase moisture
                if WATER_TANK >= water_needed:
                    WATER_TANK -= water_needed
                    
                    # Increase moisture realistically: min(20, target - current)
                    moisture_increase = min(20, field["target_moisture"] - field["current_moisture"])
                    field["current_moisture"] += moisture_increase
                    field["watering_active"] = True
                    
                    return jsonify({
                        "status": "on",
                        "water_used": water_needed,
                        "moisture_increase": moisture_increase
                    }), 200
                else:
                    return jsonify({"error": "Not enough water"}), 400
            else:
                # Turning OFF: just deactivate, water stays consumed
                field["watering_active"] = False
                return jsonify({"status": "off"}), 200
    
    return jsonify({"error": "Field not found"}), 404


# ============ Water Tank Routes ============

@app.route("/api/water-tank", methods=["GET"])
def get_water_tank():
    """Return water tank status."""
    return jsonify({
        "total": TANK_CAPACITY,
        "remaining": WATER_TANK,
        "unit": "liters"
    })


@app.route("/api/water-tank/refill", methods=["POST"])
def refill_water_tank():
    """Refill water tank with specified amount, capped at TANK_CAPACITY."""
    global WATER_TANK
    
    data = request.get_json()
    amount = data.get("amount", 0)
    
    WATER_TANK = min(WATER_TANK + amount, TANK_CAPACITY)
    
    return jsonify({
        "remaining": WATER_TANK,
        "total": TANK_CAPACITY,
        "unit": "liters"
    })


# ============ Tank Capacity Route ============

@app.route("/api/tank-capacity", methods=["POST"])
def set_tank_capacity():
    """Set a new tank capacity. Caps WATER_TANK if it exceeds new capacity."""
    global WATER_TANK, TANK_CAPACITY

    data = request.get_json()
    new_capacity = data.get("capacity", 0)

    if not isinstance(new_capacity, (int, float)) or new_capacity <= 0:
        return jsonify({"error": "Capacity must be a positive number"}), 400

    TANK_CAPACITY = int(new_capacity)
    if WATER_TANK > TANK_CAPACITY:
        WATER_TANK = TANK_CAPACITY

    return jsonify({
        "total": TANK_CAPACITY,
        "remaining": WATER_TANK,
        "unit": "liters"
    }), 200

# ============ AI Integration Routes ============

@app.route("/api/tree-knowledge", methods=["POST"])
def get_tree_knowledge():
    """
    Get optimal moisture percentage for a tree type using Gemini AI.

    Expected JSON: {"tree_type": "Orange"}
    Returns JSON: {"tree_type": "Orange", "optimal_moisture": 55}
    """
    data = request.get_json()
    tree_type = data.get("tree_type", "Unknown")

    optimal_moisture = get_tree_water_needs(tree_type)

    return jsonify({
        "tree_type": tree_type,
        "optimal_moisture": optimal_moisture
    })





# ============ Demo Reset Route ============

@app.route("/api/reset-demo", methods=["POST"])
def reset_demo():
    """
    Reset the entire demo to initial state:
    - Reset WATER_TANK to 5000
    - Restore all fields to their original current_moisture values
    - Deactivate all watering
    """
    global WATER_TANK
    
    WATER_TANK = 5000
    
    for field in FIELDS:
        # Restore original moisture value
        field["current_moisture"] = field["original_current_moisture"]
        # Deactivate watering
        field["watering_active"] = False
    
    return jsonify({
        "status": "reset",
        "message": f"✅ Demo reset! Tank restored to 5000L, {len(FIELDS)} field(s) restored to original state."
    })


# ============ AI Rationing Route ============

@app.route("/api/ai-rationing", methods=["GET"])
def ai_rationing():
    """
    Get AI-powered water rationing recommendations.
    
    Builds a description of the water tank and all fields, sends it to Gemini,
    and returns the parsed JSON response with rationing recommendations.
    
    Returns JSON with Gemini's rationing recommendations.
    """
    try:
        # Build description string
        description = f"Water Tank Status:\n"
        description += f"- Total Capacity: 5000 liters\n"
        description += f"- Current Level: {WATER_TANK} liters\n"
        description += f"- Available: {WATER_TANK} liters\n\n"
        
        description += f"Fields ({len(FIELDS)} total):\n"
        for field in FIELDS:
            description += f"- {field['name']} (ID: {field['id']})\n"
            description += f"  * Tree Type: {field['tree_type']}\n"
            description += f"  * Area: {field['area_m2']} m²\n"
            description += f"  * Current Moisture: {field['current_moisture']}%\n"
            description += f"  * Target Moisture: {field['target_moisture']}%\n"
            description += f"  * Priority: {calculate_priority(field)}\n"
            description += f"  * Water Needed: {calculate_water_needed(field)} liters\n"
        
        # Create prompt for Gemini
        prompt = f"""Analyze the following irrigation system state and provide water rationing recommendations in JSON format.

{description}

Respond with ONLY a valid JSON object (no markdown, no code blocks) with the following structure:
{{
  "total_water_available": {WATER_TANK},
  "total_water_needed": <sum of all water needed>,
  "rationing_strategy": "<brief strategy description>",
  "field_allocations": [
    {{"field_id": 1, "field_name": "name", "allocated_liters": <amount>, "reason": "explanation"}},
    ...
  ],
  "recommendations": ["<recommendation 1>", "<recommendation 2>", ...]
}}

If total water needed exceeds available water, skip lowest-priority fields. Fields with 0 liters must still appear in field_allocations with allocated_liters: 0."""
        
        # Call GitHub Models API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        
        # Strip markdown code blocks using simple string replacement
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON response
        rationing_data = json.loads(response_text)
        
        return jsonify(rationing_data), 200
    
    except json.JSONDecodeError as e:
        return jsonify({
            "error": "Failed to parse Gemini response as JSON",
            "details": str(e)
        }), 400
    
    except Exception as e:
        return jsonify({
            "error": "Failed to generate rationing recommendations",
            "details": str(e)
        }), 500


# ============ Distribution & Simulation Routes ============

@app.route("/api/distribute", methods=["GET"])
def distribute_water():
    """
    Return all fields sorted by priority (highest priority first).
    Add priority level and water_needed_liters to each field.
    """
    # Add priority and water needed to each field
    fields_with_priority = []
    for field in FIELDS:
        field_copy = field.copy()
        field_copy["priority"] = calculate_priority(field)
        field_copy["water_needed_liters"] = calculate_water_needed(field)
        fields_with_priority.append(field_copy)
    
    # Sort by priority: critical > high > medium > low
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_fields = sorted(
        fields_with_priority,
        key=lambda x: priority_order[x["priority"]]
    )
    
    return jsonify(sorted_fields)


@app.route("/api/simulate", methods=["POST"])
def simulate_sensor_data():
    """
    Simulate sensor data with realistic moisture drift.
    
    For each field:
    - If watering_active: increase moisture by 20, set watering_active=False
    - Otherwise: drift moisture by random value between -15 and +15
    - Clamp result between 10 and 95
    
    Returns summary of changes.
    """
    global WATER_TANK
    
    changes = []
    
    for field in FIELDS:
        old_moisture = field["current_moisture"]
        
        if field["watering_active"]:
            # Watering worked: increase by 20 and turn off
            field["current_moisture"] = min(95, field["current_moisture"] + 20)
            field["watering_active"] = False
            changes.append(f"{field['name']}: +20% (watering effect)")
        else:
            # Natural drift: random between -15 and +15
            drift = random.randint(-15, 15)
            field["current_moisture"] += drift
            # Clamp between 10 and 95
            field["current_moisture"] = max(10, min(95, field["current_moisture"]))
            drift_str = f"+{drift}" if drift >= 0 else f"{drift}"
            changes.append(f"{field['name']}: {drift_str}%")
    
    summary = ", ".join(changes) if changes else "No fields to simulate"
    
    return jsonify({
        "status": "ok",
        "summary": summary
    })


if __name__ == "__main__":
    app.run(debug=True)
