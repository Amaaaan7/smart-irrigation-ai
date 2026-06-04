from flask import Flask, jsonify

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True)
