from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Global data storage
FIELDS = []  # Empty list to start
WATER_TANK = 5000  # Total water tank capacity in liters
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
            display: none;
        }
        
        .message.success {
            background-color: rgba(46, 213, 115, 0.9);
            color: white;
        }
        
        .message.error {
            background-color: rgba(255, 71, 87, 0.9);
            color: white;
        }
        
        .message.show {
            display: block;
        }
        
        /* Water Tank Section */
        .water-tank-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .water-tank-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
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
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
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
        
        /* Field Cards */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .field-card {
            border-radius: 12px;
            padding: 20px;
            color: white;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
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
            background-color: rgba(255, 255, 255, 0.3);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
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
            margin: 8px 0;
        }
        
        .moisture-fill {
            background-color: rgba(255, 255, 255, 0.8);
            height: 100%;
            border-radius: 5px;
            transition: width 0.5s ease;
        }
        
        .water-needed {
            margin-top: 12px;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            font-weight: bold;
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
            <h1>🌾 Smart Irrigation Dashboard</h1>
            <p>Intelligent Water Distribution System</p>
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
                        <label for="targetMoisture">Target Moisture %</label>
                        <input type="number" id="targetMoisture" min="0" max="100" step="0.1" required>
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
        </div>
        
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
                    showMessage(`Watering ON - Used ${data.water_used} L`, 'success');
                } else if (data.status === 'off') {
                    showMessage(`Watering OFF - Returned ${data.water_returned} L`, 'success');
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
        
        // Simulate sensor data
        async function simulateSensorData() {
            try {
                const response = await fetch('/api/simulate', {
                    method: 'POST'
                });
                
                if (!response.ok) throw new Error('Simulation failed');
                
                showMessage('Sensor data simulated! Moisture levels randomized.', 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error simulating data: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Run water distribution
        async function runWaterDistribution() {
            try {
                showMessage('Running water distribution analysis...', 'success');
                await loadFields();
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
                console.error(error);
            }
        }
        
        // Show message
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = `message ${type} show`;
            
            setTimeout(() => {
                messageDiv.classList.remove('show');
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


def calculate_water_needed(field):
    """
    Calculate water needed for a field in liters.
    Formula: abs(target - current) * area_m2 * 0.01
    """
    return round(abs(field["target_moisture"] - field["current_moisture"]) * field["area_m2"] * 0.01, 2)


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
    Create a new field.
    Expected JSON: {name, tree_type, tree_count, position, area_m2, current_moisture, target_moisture}
    Auto-assigns id starting from 1.
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
    """Delete a field by id. First turn off watering if active and return water."""
    global WATER_TANK
    
    for i, field in enumerate(FIELDS):
        if field["id"] == field_id:
            # If watering is active, return water to tank
            if field["watering_active"]:
                water_needed = calculate_water_needed(field)
                WATER_TANK += water_needed
            
            FIELDS.pop(i)
            return jsonify({"status": "deleted"}), 200
    
    return jsonify({"error": "Field not found"}), 404


@app.route("/api/fields/<int:field_id>/water/toggle", methods=["POST"])
def toggle_water(field_id):
    """
    Toggle watering for a field.
    If turning ON: check if enough water, deduct from tank.
    If turning OFF: return water to tank.
    """
    global WATER_TANK
    
    for field in FIELDS:
        if field["id"] == field_id:
            water_needed = calculate_water_needed(field)
            
            if not field["watering_active"]:
                # Turning ON
                if WATER_TANK >= water_needed:
                    WATER_TANK -= water_needed
                    field["watering_active"] = True
                    return jsonify({"status": "on", "water_used": water_needed}), 200
                else:
                    return jsonify({"error": "Not enough water"}), 400
            else:
                # Turning OFF
                WATER_TANK += water_needed
                field["watering_active"] = False
                return jsonify({"status": "off", "water_returned": water_needed}), 200
    
    return jsonify({"error": "Field not found"}), 404


# ============ Water Tank Routes ============

@app.route("/api/water-tank", methods=["GET"])
def get_water_tank():
    """Return water tank status."""
    return jsonify({
        "total": 5000,
        "remaining": WATER_TANK,
        "unit": "liters"
    })


@app.route("/api/water-tank/refill", methods=["POST"])
def refill_water_tank():
    """Refill water tank with specified amount."""
    global WATER_TANK
    
    data = request.get_json()
    amount = data.get("amount", 0)
    
    WATER_TANK += amount
    
    return jsonify({
        "remaining": WATER_TANK,
        "total": 5000,
        "unit": "liters"
    })


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
    Simulate sensor data by randomizing current_moisture for all fields.
    Moisture values are randomized between 20-80.
    If any field has watering_active=True, set it to False (safety reset).
    """
    global WATER_TANK
    
    for field in FIELDS:
        # If watering is active, turn it off and return water
        if field["watering_active"]:
            water_needed = calculate_water_needed(field)
            WATER_TANK += water_needed
            field["watering_active"] = False
        
        # Randomize moisture
        field["current_moisture"] = random.randint(20, 80)
    
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
