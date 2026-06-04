from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# List of farm fields with irrigation data
FIELDS = [
    {
        "id": 1,
        "name": "North Field",
        "tree_type": "Apple",
        "area_m2": 5000,
        "current_moisture": 45,
        "target_moisture": 60
    },
    {
        "id": 2,
        "name": "South Field",
        "tree_type": "Orange",
        "area_m2": 4500,
        "current_moisture": 25,
        "target_moisture": 55
    },
    {
        "id": 3,
        "name": "East Field",
        "tree_type": "Mango",
        "area_m2": 6000,
        "current_moisture": 35,
        "target_moisture": 65
    },
    {
        "id": 4,
        "name": "West Field",
        "tree_type": "Coconut",
        "area_m2": 3500,
        "current_moisture": 70,
        "target_moisture": 75
    }
]

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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        button {
            background-color: white;
            color: #667eea;
            border: none;
            padding: 12px 24px;
            font-size: 1em;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .loading {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .field-card {
            border-radius: 10px;
            padding: 20px;
            color: white;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
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
        
        .field-card h3 {
            font-size: 1.4em;
            margin-bottom: 8px;
        }
        
        .field-card p {
            font-size: 0.9em;
            margin-bottom: 12px;
            opacity: 0.95;
        }
        
        .priority-badge {
            display: inline-block;
            background-color: rgba(255, 255, 255, 0.3);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 10px;
        }
        
        .moisture-info {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .moisture-bar {
            background-color: rgba(255, 255, 255, 0.3);
            height: 8px;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .moisture-fill {
            background-color: rgba(255, 255, 255, 0.8);
            height: 100%;
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        .error {
            background-color: rgba(255, 71, 87, 0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .success {
            background-color: rgba(46, 213, 115, 0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌾 Smart Irrigation Dashboard</h1>
            <p>Intelligent Water Distribution System</p>
        </div>
        
        <div class="controls">
            <button onclick="simulateSensorData()">Simulate Sensor Data</button>
            <button onclick="runWaterDistribution()">Run Water Distribution</button>
        </div>
        
        <div id="message"></div>
        <div class="cards-grid" id="fieldsContainer">
            <p style="color: white; text-align: center; grid-column: 1/-1;">Loading fields...</p>
        </div>
    </div>
    
    <script>
        // Fetch and display fields from /api/distribute
        async function loadFields() {
            try {
                const response = await fetch('/api/distribute');
                if (!response.ok) throw new Error('Failed to load fields');
                const fields = await response.json();
                displayFields(fields);
            } catch (error) {
                showMessage('Error loading fields: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Display fields as colored cards
        function displayFields(fields) {
            const container = document.getElementById('fieldsContainer');
            container.innerHTML = '';
            
            fields.forEach(field => {
                const moisturePercent = Math.round((field.current_moisture / field.target_moisture) * 100);
                const card = document.createElement('div');
                card.className = `field-card ${field.priority}`;
                
                card.innerHTML = `
                    <h3>${field.name}</h3>
                    <p><strong>Tree Type:</strong> ${field.tree_type}</p>
                    <p><strong>Area:</strong> ${field.area_m2} m²</p>
                    
                    <div class="moisture-info">
                        <p><strong>Current Moisture:</strong> ${field.current_moisture}%</p>
                        <p><strong>Target Moisture:</strong> ${field.target_moisture}%</p>
                        <div class="moisture-bar">
                            <div class="moisture-fill" style="width: ${moisturePercent}%"></div>
                        </div>
                    </div>
                    
                    <span class="priority-badge">${field.priority}</span>
                `;
                
                container.appendChild(card);
            });
        }
        
        // Simulate sensor data by randomizing moisture levels
        async function simulateSensorData() {
            try {
                const response = await fetch('/api/simulate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) throw new Error('Simulation failed');
                const result = await response.json();
                
                showMessage('Sensor data simulated successfully! Moisture levels randomized.', 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error simulating sensor data: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Refresh display with /api/distribute
        async function runWaterDistribution() {
            try {
                showMessage('Running water distribution analysis...', 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error running distribution: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Show message alert
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.className = type;
            messageDiv.textContent = text;
            
            // Clear message after 4 seconds
            setTimeout(() => {
                messageDiv.textContent = '';
                messageDiv.className = '';
            }, 4000);
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
    - critical: current_moisture < 30
    - high: current_moisture < target_moisture - 10
    - medium: current_moisture < target_moisture
    - low: otherwise
    """
    current = field["current_moisture"]
    target = field["target_moisture"]
    
    if current < 30:
        return "critical"
    elif current < target - 10:
        return "high"
    elif current < target:
        return "medium"
    else:
        return "low"


@app.route("/", methods=["GET"])
def home():
    """Render the HTML dashboard."""
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/fields", methods=["GET"])
def get_all_fields():
    """Return all fields as JSON."""
    return jsonify(FIELDS)


@app.route("/api/fields/<int:field_id>", methods=["GET"])
def get_field(field_id):
    """Return a specific field by ID."""
    for field in FIELDS:
        if field["id"] == field_id:
            return jsonify(field)
    
    return jsonify({"error": "Field not found"}), 404


@app.route("/api/distribute", methods=["GET"])
def distribute_water():
    """
    Return all fields sorted by priority (highest priority first).
    Add priority level to each field.
    """
    # Add priority to each field
    fields_with_priority = []
    for field in FIELDS:
        field_copy = field.copy()
        field_copy["priority"] = calculate_priority(field)
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
    Simulate sensor data by randomizing current_moisture for all fields.
    Moisture values are randomized between 20-80.
    """
    for field in FIELDS:
        field["current_moisture"] = random.randint(20, 80)
    
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
