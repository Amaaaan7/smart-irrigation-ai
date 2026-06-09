from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import random
import re
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

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
WATER_TANK = 3200
TANK_CAPACITY = 5000
NEXT_FIELD_ID = 5

FIELDS = [
    {
        "id": 1,
        "name": "North Orchard",
        "tree_type": "Orange",
        "tree_count": 50,
        "position": "North",
        "area_m2": 2000,
        "current_moisture": 22,
        "target_moisture": 60,
        "watering_active": False,
        "original_current_moisture": 22
    },
    {
        "id": 2,
        "name": "South Grove",
        "tree_type": "Olive",
        "tree_count": 80,
        "position": "South",
        "area_m2": 3500,
        "current_moisture": 30,
        "target_moisture": 55,
        "watering_active": False,
        "original_current_moisture": 30
    },
    {
        "id": 3,
        "name": "East Field",
        "tree_type": "Apple",
        "tree_count": 30,
        "position": "East",
        "area_m2": 1200,
        "current_moisture": 52,
        "target_moisture": 65,
        "watering_active": False,
        "original_current_moisture": 52
    },
    {
        "id": 4,
        "name": "West Vineyard",
        "tree_type": "Grape",
        "tree_count": 120,
        "position": "West",
        "area_m2": 4000,
        "current_moisture": 70,
        "target_moisture": 60,
        "watering_active": False,
        "original_current_moisture": 70
    }
]

# JSON persistence file
DATA_FILE = "data.json"

# Seasonal cache for tree types
SEASON_CACHE = {}

# Water tracking for AI efficiency
WATER_AI_USED = 0
WATER_MANUAL_USED = 0

# Moisture history for charting
MOISTURE_HISTORY = {}

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Irrigation Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.css">
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

        .emergency-banner {
            display: none;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 1.1em;
            animation: slideIn 0.3s ease;
        }

        .emergency-banner.show {
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

        .efficiency-stat {
            font-size: 0.95em;
            color: #333;
            margin-top: 10px;
            padding: 8px;
            background: #f0fdf4;
            border-radius: 6px;
            font-weight: 500;
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

        .btn-emergency {
            background-color: #ef4444;
            color: white;
            border: 2px solid #dc2626;
            padding: 12px 24px;
            font-size: 1em;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }

        .btn-emergency:hover {
            background-color: #dc2626;
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

        .season-badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 20px;
            font-weight: 500;
            margin-left: 6px;
            display: inline-block;
        }

        .in-season {
            background: #dcfce7;
            color: #166534;
        }

        .off-season {
            background: #f1f5f9;
            color: #64748b;
        }

        .seasonal-boost-banner {
            margin-top: 12px;
            padding: 10px;
            background: #f0fdf4;
            border-radius: 6px;
            color: #166534;
            font-weight: 500;
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

        .history-section {
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .history-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
        }

        #historyChart {
            max-height: 400px;
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
        <div id="emergencyBanner" class="emergency-banner"></div>
        
        <!-- Water Tank Section -->
        <div class="water-tank-section">
            <div class="water-tank-card" id="tankCard">
                <h2>💧 Water Tank Status</h2>
                <div class="water-status" id="waterStatus">5000 / 5000 L</div>
                <div class="water-bar">
                    <div class="water-fill" id="waterFill" style="width: 100%"></div>
                </div>
                <div class="water-info">Tank Capacity: 5000 liters</div>
                <div class="efficiency-stat" id="efficiencyStat" style="display: none;">
                    💧 AI efficiency: saved <span id="efficiencyPercent">0</span>% vs full manual watering
                </div>
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
            <button onclick="triggerEmergencyMode()" class="btn-emergency">🚨 Emergency Mode</button>
            <button onclick="resetDemo()" class="btn-secondary">Reset Demo</button>
        </div>
        
        <!-- AI Rationing Plan Container -->
        <div id="aiPlanContainer"></div>

        <!-- Moisture History Chart -->
        <div class="history-section" id="historySection" style="display: none;">
            <h2>📊 Moisture History</h2>
            <canvas id="historyChart"></canvas>
        </div>
        
        <!-- Field Cards -->
        <div class="cards-grid" id="fieldsContainer">
            <div class="empty-state">No fields yet. Add a field to get started!</div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <script>
        let currentPlan = null;
        let seasonData = {};
        let historyChart = null;

        // Calculate water needed for a field
        function calculateWaterNeeded(field) {
            return Math.round(Math.max(0, field.target_moisture - field.current_moisture) * field.area_m2 * 0.01 * 100) / 100;
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

        // Load seasonal data
        async function loadSeasonData() {
            try {
                const response = await fetch('/api/season');
                if (!response.ok) throw new Error('Failed to load season data');
                const data = await response.json();
                if (data.results) {
                    data.results.forEach(item => {
                        seasonData[item.tree_type] = item;
                    });
                }
            } catch (error) {
                console.error('Error loading season data:', error);
                seasonData = {};
            }
        }

        // Load water efficiency data
        async function loadWaterEfficiency() {
            try {
                const response = await fetch('/api/savings');
                if (!response.ok) throw new Error('Failed to load savings data');
                const data = await response.json();
                const efficiencyPercent = Math.round(data.savings_percent);
                if (efficiencyPercent > 0) {
                    document.getElementById('efficiencyStat').style.display = 'block';
                    document.getElementById('efficiencyPercent').textContent = efficiencyPercent;
                }
            } catch (error) {
                console.error('Error loading water efficiency:', error);
            }
        }

        // Load moisture history and draw chart
        async function loadMoistureHistory() {
            try {
                const response = await fetch('/api/history');
                if (!response.ok) throw new Error('Failed to load history');
                const history = await response.json();

                const fieldsRes = await fetch('/api/fields');
                if (!fieldsRes.ok) throw new Error('Failed to load fields');
                const fields = await fieldsRes.json();

                if (Object.keys(history).length === 0) {
                    document.getElementById('historySection').style.display = 'none';
                    return;
                }

                document.getElementById('historySection').style.display = 'block';

                const datasets = [];
                const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];

                fields.forEach((field, idx) => {
                    const fieldId = String(field.id);
                    if (history[fieldId]) {
                        datasets.push({
                            label: field.name,
                            data: history[fieldId],
                            borderColor: colors[idx % colors.length],
                            backgroundColor: colors[idx % colors.length] + '20',
                            tension: 0.1,
                            fill: false
                        });
                    }
                });

                const ctx = document.getElementById('historyChart').getContext('2d');
                if (historyChart) historyChart.destroy();
                historyChart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: Array.from({length: Math.max(...datasets.map(d => d.data.length))}, (_, i) => `Reading ${i+1}`), datasets },
                    options: {
                        responsive: true,
                        plugins: { legend: { position: 'top' } },
                        scales: { y: { beginAtZero: true, max: 100 } }
                    }
                });
            } catch (error) {
                console.error('Error loading history:', error);
            }
        }

        // Trigger emergency mode
        async function triggerEmergencyMode() {
            try {
                const tankRes = await fetch('/api/water-tank');
                const tankData = await tankRes.json();
                const percent = (tankData.remaining / tankData.total) * 100;

                if (percent < 20) {
                    showEmergencyBanner();
                    await generateRationingPlan();
                    await new Promise(r => setTimeout(r, 500));
                    await applyRationingPlan();
                } else {
                    showMessage('⚠️ Tank levels OK — emergency not needed', 'info');
                }
            } catch (error) {
                showMessage('Error in emergency mode: ' + error.message, 'error');
            }
        }

        function showEmergencyBanner() {
            const banner = document.getElementById('emergencyBanner');
            banner.textContent = '⚠️ Emergency rationing active';
            banner.classList.add('show');
        }

        function hideEmergencyBanner() {
            const banner = document.getElementById('emergencyBanner');
            banner.classList.remove('show');
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
                loadWaterEfficiency();
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
            
            // Warning color when tank is below 20%
            const fillBar = document.getElementById('waterFill');
            const tankCard = document.getElementById('tankCard');
            
            if (percent <= 20) {
                fillBar.style.background = 'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)';
                tankCard.style.border = '2px solid #ef4444';
                tankCard.style.boxShadow = '0 0 20px rgba(239, 68, 68, 0.3)';
            } else {
                fillBar.style.background = 'linear-gradient(90deg, #0ea5e9 0%, #06b6d4 100%)';
                tankCard.style.border = '1px solid rgba(255, 255, 255, 0.3)';
                tankCard.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.1)';
            }
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

                const inSeason = seasonData[field.tree_type]?.in_season ?? true;
                const seasonBadge = inSeason 
                    ? '<span class="season-badge in-season">🌿 Peak Season</span>'
                    : '<span class="season-badge off-season">💤 Off Season</span>';
                
                card.innerHTML = `
                    <div class="field-card-header">
                        <div>
                            <h3>${field.name}</h3>
                            <p><strong>ID:</strong> ${field.id}</p>
                        </div>
                        <button class="delete-btn" onclick="deleteField(${field.id})">Delete</button>
                    </div>
                    
                    <p><strong>Tree Type:</strong> ${field.tree_type} ${seasonBadge}</p>
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
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({manual: true})
                });
                
                const data = await response.json();
                
                if (response.status === 400) {
                    showMessage('Error: ' + data.error, 'error');
                    return;
                }
                
                if (data.status === 'on') {
                    showMessage(`✅ Watering ON - Used ${data.water_used} L, moisture increased by ${data.moisture_increase}%`, 'success');
                } else if (data.status === 'off') {
                    showMessage(`🛑 Watering OFF - Pump stopped`, 'success');
                }
                
                await loadFields();
                await loadMoistureHistory();
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
                await loadMoistureHistory();
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
                
                currentPlan = plan;
                
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

                const hasInSeason = plan.field_allocations && plan.field_allocations.some(a => a.in_season && a.allocated_liters > 0);
                if (hasInSeason) {
                    html += `
                        <div class="seasonal-boost-banner" style="grid-column: 1 / -1;">
                            🌿 Seasonal boost applied to in-season crops (AI-determined)
                        </div>
                    `;
                }
                
                html += `
                    </div>
                    <div style="margin-top: 24px; text-align: center;">
                        <button onclick="applyRationingPlan()" style="background: linear-gradient(135deg, #667eea 0%, #22c55e 100%); color: white; border: none; padding: 14px 32px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 1em; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                            ⚡ Apply Plan — Activate Fields Now
                        </button>
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
        // Apply AI rationing plan

        async function applyRationingPlan() {
            if (!currentPlan) {
                showMessage('No plan to apply. Generate a plan first.', 'error');
                return;
            }

            let activated = 0;

            for (const allocation of currentPlan.field_allocations) {
                if (allocation.allocated_liters > 0) {
                    const fieldsRes = await fetch('/api/fields');
                    const fields = await fieldsRes.json();
                    const field = fields.find(f => f.id === allocation.field_id);

                    if (field && !field.watering_active) {
                       const res = await fetch(`/api/fields/${allocation.field_id}/water/toggle`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({auto: true})
                        });
                        if (res.ok) activated++;
                    }
                }
            }

            hideEmergencyBanner();
            showMessage(`✅ AI plan applied! ${activated} field(s) activated.`, 'success');
            await loadFields();
            await loadMoistureHistory();
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
                hideEmergencyBanner();
                
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
        window.addEventListener('load', async () => {
            await loadFields();
            await loadSeasonData();
            await loadMoistureHistory();
        });
    </script>
</body>
</html>
"""


def save_state():
    """Save current state to data.json"""
    try:
        state = {
            "FIELDS": FIELDS,
            "WATER_TANK": WATER_TANK,
            "TANK_CAPACITY": TANK_CAPACITY,
            "NEXT_FIELD_ID": NEXT_FIELD_ID,
            "WATER_AI_USED": WATER_AI_USED,
            "WATER_MANUAL_USED": WATER_MANUAL_USED
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")


def load_state():
    """Load state from data.json"""
    global FIELDS, WATER_TANK, TANK_CAPACITY, NEXT_FIELD_ID, WATER_AI_USED, WATER_MANUAL_USED
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                state = json.load(f)
                FIELDS = state.get("FIELDS", FIELDS)
                WATER_TANK = state.get("WATER_TANK", WATER_TANK)
                TANK_CAPACITY = state.get("TANK_CAPACITY", TANK_CAPACITY)
                NEXT_FIELD_ID = state.get("NEXT_FIELD_ID", NEXT_FIELD_ID)
                WATER_AI_USED = state.get("WATER_AI_USED", 0)
                WATER_MANUAL_USED = state.get("WATER_MANUAL_USED", 0)
    except Exception as e:
        print(f"Error loading state: {e}")


def get_seasonal_status(tree_types):
    """Determine seasonal irrigation status for crops using AI"""
    if not tree_types:
        return {}
    
    unique_types = list(set(tree_types))
    
    # Check cache first
    result = {}
    uncached = [t for t in unique_types if t not in SEASON_CACHE]
    
    if not uncached:
        return {t: SEASON_CACHE.get(t, True) for t in unique_types}
    
    try:
        from datetime import datetime
        month_name = datetime.now().strftime("%B")
        
        prompt = f"""Today is {month_name} in a Mediterranean climate. For each crop: {uncached}, determine which are in their PEAK irrigation season (critical growth phase: fruit development, fruit set, berry sizing, or oil accumulation). Respond with ONLY a JSON object like {{"Orange": true, "Olive": false}}. No explanation, no markdown."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        seasonal_data = json.loads(response_text)
        
        for tree_type in uncached:
            status = seasonal_data.get(tree_type, True)
            SEASON_CACHE[tree_type] = status
        
        result = {t: SEASON_CACHE.get(t, True) for t in unique_types}
        return result
    
    except Exception as e:
        print(f"Error getting seasonal status: {e}")
        return {t: True for t in unique_types}


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
    Use GitHub Models AI to get optimal soil moisture percentage for a tree type.
    Uses GPT-4o-mini via the OpenAI-compatible GitHub Models endpoint.
    
    Args:
        tree_type (str): Name of the tree type (e.g., "Orange", "Apple")
    
    Returns:
        int: Optimal soil moisture percentage (0-100), defaults to 60 if API fails
    """
    try:
        # Create prompt for Github models 
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
        print(f"Error calling GitHub Models API: {e}")
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
    save_state()
    
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
            save_state()
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
    global WATER_TANK, WATER_AI_USED, WATER_MANUAL_USED
    
    for field in FIELDS:
        if field["id"] == field_id:
            water_needed = calculate_water_needed(field)
            
            data = request.get_json(force=True, silent=True) or {}  
            auto_fill = data.get("auto", False)
            manual = data.get("manual", False)
            
            if not field["watering_active"]:
                # Turning ON
                
                # Auto-fill logic: fill to target in one go, even if tank is low
                if auto_fill and water_needed > 0:
                    available = min(WATER_TANK, water_needed)
                    if available <= 0:
                        return jsonify({"error": "Not enough water"}), 400
                    ratio = available / water_needed
                    deficit = field["target_moisture"] - field["current_moisture"]
                    moisture_gain = round(deficit * ratio, 1)
                    WATER_TANK -= available
                    WATER_AI_USED += available
                    field["current_moisture"] = round(field["current_moisture"] + moisture_gain, 1)
                    field["watering_active"] = True
                    save_state()
                    return jsonify({
                        "status": "on",
                        "water_used": round(available, 2),
                        "moisture_increase": moisture_gain
                    }), 200
                
                # Normal toggle: one burst only
                if WATER_TANK >= water_needed:
                    WATER_TANK -= water_needed
                    if manual:
                        WATER_MANUAL_USED += water_needed
                    moisture_increase = max(0, min(20, field["target_moisture"] - field["current_moisture"]))
                    field["current_moisture"] += moisture_increase
                    field["watering_active"] = True
                    save_state()
                    return jsonify({
                        "status": "on",
                        "water_used": water_needed,
                        "moisture_increase": moisture_increase
                    }), 200
                else:
                    return jsonify({"error": "Not enough water"}), 400
            
            else:
                # Turning OFF
                field["watering_active"] = False
                save_state()
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
    save_state()
    
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
    
    save_state()

    return jsonify({
        "total": TANK_CAPACITY,
        "remaining": WATER_TANK,
        "unit": "liters"
    }), 200

# ============ AI Integration Routes ============

@app.route("/api/tree-knowledge", methods=["POST"])
def get_tree_knowledge():
    """
    Get optimal moisture percentage for a tree type using GitHub Models AI.

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


@app.route("/api/season", methods=["GET"])
def get_season_data():
    """Get seasonal status for all crops"""
    try:
        tree_types = [f["tree_type"] for f in FIELDS]
        seasonal_status = get_seasonal_status(tree_types)
        
        from datetime import datetime
        month_name = datetime.now().strftime("%B")
        
        results = []
        for tree_type in tree_types:
            results.append({
                "tree_type": tree_type,
                "in_season": seasonal_status.get(tree_type, True),
                "current_month": month_name
            })
        
        return jsonify({"results": results, "source": "ai"})
    except Exception as e:
        return jsonify({"results": [], "error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_moisture_history():
    """Get moisture history for all fields"""
    return jsonify(MOISTURE_HISTORY)


@app.route("/api/savings", methods=["GET"])
def get_water_savings():
    """Get water savings data comparing AI vs manual watering"""
    total_water_needed = sum(calculate_water_needed(f) for f in FIELDS)
    manual_cost = total_water_needed if total_water_needed > 0 else 1
    
    savings_percent = 0
    if WATER_AI_USED < manual_cost:
        savings_percent = ((manual_cost - WATER_AI_USED) / manual_cost) * 100
    
    return jsonify({
        "water_ai_used": round(WATER_AI_USED, 2),
        "water_manual_used": round(WATER_MANUAL_USED, 2),
        "total_water_needed": round(manual_cost, 2),
        "savings_percent": round(savings_percent, 1)
    })


# ============ Demo Reset Route ============

@app.route("/api/reset-demo", methods=["POST"])
def reset_demo():
    """
    Reset the entire demo to initial state:
    - Reset WATER_TANK to TANK_CAPACITY
    - Restore all fields to their original current_moisture values
    - Deactivate all watering
    - Clear history and water tracking
    """
    global WATER_TANK, WATER_AI_USED, WATER_MANUAL_USED, MOISTURE_HISTORY
    
    WATER_TANK = TANK_CAPACITY
    WATER_AI_USED = 0
    WATER_MANUAL_USED = 0
    MOISTURE_HISTORY = {}
    
    for field in FIELDS:
        # Restore original moisture value
        field["current_moisture"] = field["original_current_moisture"]
        # Deactivate watering
        field["watering_active"] = False
    
    save_state()
    
    return jsonify({
        "status": "reset",
        "message": f"✅ Demo reset! Tank restored to {TANK_CAPACITY}L, {len(FIELDS)} field(s) restored to original state."
    })


# ============ AI Rationing Route ============

@app.route("/api/ai-rationing", methods=["GET"])
def ai_rationing():
    """
    Get AI-powered water rationing recommendations with FAIR DISTRIBUTION.
    
    Key fix: Distributes water proportionally across priority levels rather than 
    giving all to highest priority first. This ensures all critical fields get water.
    """
    try:
        # Get seasonal status
        tree_types = [f["tree_type"] for f in FIELDS]
        seasonal_status = get_seasonal_status(tree_types)
        
        # Build description string with seasonal context
        description = f"Water Tank Status:\n"
        description += f"- Total Capacity: {TANK_CAPACITY} liters\n"
        description += f"- Current Level: {WATER_TANK} liters\n"
        description += f"- Available: {WATER_TANK} liters\n\n"
        
        description += f"Fields ({len(FIELDS)} total):\n"
        for field in FIELDS:
            in_season = seasonal_status.get(field['tree_type'], True)
            season_text = "(PEAK SEASON)" if in_season else "(OFF SEASON)"
            description += f"- {field['name']} (ID: {field['id']}) {season_text}\n"
            description += f"  * Tree Type: {field['tree_type']}\n"
            description += f"  * Area: {field['area_m2']} m²\n"
            description += f"  * Current Moisture: {field['current_moisture']}%\n"
            description += f"  * Target Moisture: {field['target_moisture']}%\n"
            description += f"  * Priority: {calculate_priority(field)}\n"
            description += f"  * Water Needed: {calculate_water_needed(field)} liters\n"
            description += f"  * Seasonal Status: {'PEAK' if in_season else 'OFF'} season\n"
        
        # Create prompt with emphasis on fair distribution and seasonal priority
        prompt = f"""Analyze the following irrigation system state and provide water rationing recommendations in JSON format.

{description}

CRITICAL RULES FOR DISTRIBUTION:
1. Do NOT give all water to one field first. DISTRIBUTE FAIRLY across priority levels.
2. If there are multiple CRITICAL fields, split available water proportionally among them.
3. After critical fields, allocate remaining water proportionally to HIGH priority fields.
4. In-season crops must receive approximately 25% higher allocation weight than off-season crops when moisture levels are similar.
5. ALL critical and high priority fields should receive SOME water if available, not zero.
6. Only skip fields (allocate 0) if water is truly exhausted or field has LOW priority.

Respond with ONLY a valid JSON object (no markdown, no code blocks) with the following structure:
{{
  "total_water_available": {WATER_TANK},
  "total_water_needed": <sum of all water needed>,
  "rationing_strategy": "<brief strategy description mentioning FAIR DISTRIBUTION across priority levels>",
  "field_allocations": [
    {{"field_id": 1, "field_name": "name", "allocated_liters": <amount>, "reason": "explanation", "in_season": true/false}},
    ...
  ],
  "recommendations": ["<recommendation 1>", "<recommendation 2>", ...]
}}

IMPORTANT: Every field must appear in field_allocations. Use proportional distribution, not first-come-first-served."""
        
        # Call GitHub Models API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
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
            "error": "Failed to parse AI response as JSON",
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
    
    Track moisture history for charting.
    Returns summary of changes.
    """
    global WATER_TANK
    
    changes = []
    
    for field in FIELDS:
        old_moisture = field["current_moisture"]
        field_id = str(field["id"])
        
        # Initialize history if needed
        if field_id not in MOISTURE_HISTORY:
            MOISTURE_HISTORY[field_id] = []
        
        if field["watering_active"]:
            # Watering worked: gradual increase and turn off
            field["current_moisture"] = min(95, field["current_moisture"] + random.uniform(2, 5))
            field["watering_active"] = False
            changes.append(f"{field['name']}: +20% (watering effect)")
        else:
            # Natural drift: slow drying, slight recovery possible
            drift = random.uniform(-3, -1)
            field["current_moisture"] += drift
            # Clamp between 10 and 95
            field["current_moisture"] = max(10, min(95, field["current_moisture"]))
            drift_str = f"+{drift}" if drift >= 0 else f"{drift}"
            changes.append(f"{field['name']}: {drift_str}%")
        
        # Cap history at 10 readings per field
        MOISTURE_HISTORY[field_id].append(round(field["current_moisture"], 1))
        if len(MOISTURE_HISTORY[field_id]) > 10:
            MOISTURE_HISTORY[field_id].pop(0)
    
    save_state()
    
    summary = ", ".join(changes) if changes else "No fields to simulate"
    
    return jsonify({
        "status": "ok",
        "summary": summary
    })


if __name__ == "__main__":
    load_state()
    app.run(debug=True)
