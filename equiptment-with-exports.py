# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
import json
import os
import csv
import io
from datetime import datetime
from typing import List, Dict, Optional

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

class EquipmentTracker:
    def __init__(self, data_file: str = "equipment_data.json"):
        self.data_file = data_file
        self.equipment_list = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load equipment data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_data(self):
        """Save equipment data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.equipment_list, f, indent=2, default=str)
    
    def _get_next_id(self) -> int:
        """Get the next available ID"""
        if not self.equipment_list:
            return 1
        return max(item['id'] for item in self.equipment_list) + 1
    
    def add_equipment(self, description: str, cost: float, purchase_date: str = None,
                     current_retail: float = 0.0, current_resale: float = 0.0,
                     resale_location: str = "", condition: str = "Good"):
        """Add new equipment to the tracker"""
        if purchase_date is None or purchase_date == "":
            purchase_date = datetime.now().strftime("%Y-%m-%d")
        
        equipment = {
            "id": self._get_next_id(),
            "description": description,
            "cost": float(cost),
            "purchase_date": purchase_date,
            "current_retail": float(current_retail),
            "current_resale": float(current_resale),
            "resale_location": resale_location,
            "condition": condition,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.equipment_list.append(equipment)
        self._save_data()
        return equipment['id']
    
    def update_equipment(self, equipment_id: int, **kwargs):
        """Update existing equipment"""
        for equipment in self.equipment_list:
            if equipment['id'] == equipment_id:
                for key, value in kwargs.items():
                    if key in equipment and value is not None and value != "":
                        if key in ['cost', 'current_retail', 'current_resale']:
                            equipment[key] = float(value)
                        else:
                            equipment[key] = value
                equipment['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_data()
                return True
        return False
    
    def delete_equipment(self, equipment_id: int):
        """Delete equipment by ID"""
        for i, equipment in enumerate(self.equipment_list):
            if equipment['id'] == equipment_id:
                self.equipment_list.pop(i)
                self._save_data()
                return True
        return False
    
    def search_equipment(self, query: str) -> List[Dict]:
        """Search equipment by description"""
        if not query:
            return self.equipment_list
        results = []
        query_lower = query.lower()
        for equipment in self.equipment_list:
            if (query_lower in equipment['description'].lower() or 
                query_lower in equipment['condition'].lower() or
                query_lower in equipment['resale_location'].lower()):
                results.append(equipment)
        return results
    
    def get_all_equipment(self) -> List[Dict]:
        """Get all equipment"""
        return sorted(self.equipment_list, key=lambda x: x['id'], reverse=True)
    
    def get_equipment_by_id(self, equipment_id: int) -> Optional[Dict]:
        """Get equipment by ID"""
        for equipment in self.equipment_list:
            if equipment['id'] == equipment_id:
                return equipment
        return None
    
    def get_total_value(self) -> Dict[str, float]:
        """Calculate total values"""
        total_cost = sum(item['cost'] for item in self.equipment_list)
        total_retail = sum(item['current_retail'] for item in self.equipment_list)
        total_resale = sum(item['current_resale'] for item in self.equipment_list)
        
        return {
            'total_cost': total_cost,
            'total_retail': total_retail,
            'total_resale': total_resale,
            'profit_loss': total_resale - total_cost,
            'count': len(self.equipment_list)
        }

# Initialize tracker
tracker = EquipmentTracker()

@app.route('/')
def index():
    """Main dashboard"""
    equipment_list = tracker.get_all_equipment()
    summary = tracker.get_total_value()
    return render_template('index.html', equipment_list=equipment_list, summary=summary)

@app.route('/add', methods=['GET', 'POST'])
def add_equipment():
    """Add new equipment"""
    if request.method == 'POST':
        try:
            description = request.form.get('description', '').strip()
            cost = float(request.form.get('cost', 0))
            purchase_date = request.form.get('purchase_date', '')
            current_retail = float(request.form.get('current_retail', 0) or 0)
            current_resale = float(request.form.get('current_resale', 0) or 0)
            resale_location = request.form.get('resale_location', '').strip()
            condition = request.form.get('condition', 'Good')
            
            if not description:
                flash('Description is required!', 'error')
                return render_template('add.html')
            
            equipment_id = tracker.add_equipment(
                description, cost, purchase_date, current_retail, 
                current_resale, resale_location, condition
            )
            
            flash(f'Equipment "{description}" added successfully!', 'success')
            return redirect(url_for('index'))
            
        except ValueError as e:
            flash('Invalid numeric value entered!', 'error')
        except Exception as e:
            flash(f'Error adding equipment: {str(e)}', 'error')
    
    return render_template('add.html')

@app.route('/edit/<int:equipment_id>', methods=['GET', 'POST'])
def edit_equipment(equipment_id):
    """Edit existing equipment"""
    equipment = tracker.get_equipment_by_id(equipment_id)
    if not equipment:
        flash('Equipment not found!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            updates = {
                'description': request.form.get('description', '').strip(),
                'cost': request.form.get('cost'),
                'purchase_date': request.form.get('purchase_date'),
                'current_retail': request.form.get('current_retail') or 0,
                'current_resale': request.form.get('current_resale') or 0,
                'resale_location': request.form.get('resale_location', '').strip(),
                'condition': request.form.get('condition')
            }
            
            # Filter out empty values
            updates = {k: v for k, v in updates.items() if v != ''}
            
            if tracker.update_equipment(equipment_id, **updates):
                flash('Equipment updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Error updating equipment!', 'error')
                
        except ValueError:
            flash('Invalid numeric value entered!', 'error')
        except Exception as e:
            flash(f'Error updating equipment: {str(e)}', 'error')
    
    return render_template('edit.html', equipment=equipment)

@app.route('/delete/<int:equipment_id>')
def delete_equipment(equipment_id):
    """Delete equipment"""
    equipment = tracker.get_equipment_by_id(equipment_id)
    if equipment:
        if tracker.delete_equipment(equipment_id):
            flash(f'Equipment "{equipment["description"]}" deleted successfully!', 'success')
        else:
            flash('Error deleting equipment!', 'error')
    else:
        flash('Equipment not found!', 'error')
    
    return redirect(url_for('index'))

@app.route('/search')
def search():
    """Search equipment"""
    query = request.args.get('q', '').strip()
    equipment_list = tracker.search_equipment(query)
    summary = tracker.get_total_value()
    return render_template('index.html', equipment_list=equipment_list, summary=summary, search_query=query)

@app.route('/export/csv')
def export_csv():
    """Export all equipment to CSV"""
    equipment_list = tracker.get_all_equipment()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Description', 'Purchase Cost', 'Purchase Date', 
        'Current Retail', 'Current Resale', 'Resale Location', 
        'Condition', 'Date Added', 'Last Updated', 'Profit/Loss'
    ])
    
    # Write data
    for equipment in equipment_list:
        profit_loss = equipment.get('current_resale', 0) - equipment.get('cost', 0)
        writer.writerow([
            equipment.get('id', ''),
            equipment.get('description', ''),
            equipment.get('cost', 0),
            equipment.get('purchase_date', ''),
            equipment.get('current_retail', 0),
            equipment.get('current_resale', 0),
            equipment.get('resale_location', ''),
            equipment.get('condition', ''),
            equipment.get('date_added', ''),
            equipment.get('last_updated', ''),
            profit_loss
        ])
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"equipment_export_{timestamp}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/api/summary')
def api_summary():
    """API endpoint for summary data"""
    return jsonify(tracker.get_total_value())

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create base template
    with open('templates/base.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Equipment Tracker{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .card-stats { border-left: 4px solid #007bff; }
        .profit-positive { color: #28a745; }
        .profit-negative { color: #dc3545; }
        .table-actions { width: 120px; }
        .search-box { max-width: 400px; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-tools me-2"></i>Equipment Tracker
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
                <a class="nav-link" href="{{ url_for('add_equipment') }}">
                    <i class="fas fa-plus me-1"></i>Add Equipment
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>''')
    
    # Create index template
    with open('templates/index.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block content %}
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card card-stats">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <p class="card-category text-muted">Total Items</p>
                        <h3 class="card-title">{{ summary.count }}</h3>
                    </div>
                    <div class="icon">
                        <i class="fas fa-boxes fa-2x text-primary"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card card-stats">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <p class="card-category text-muted">Total Cost</p>
                        <h3 class="card-title">${{ "%.2f"|format(summary.total_cost) }}</h3>
                    </div>
                    <div class="icon">
                        <i class="fas fa-dollar-sign fa-2x text-success"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card card-stats">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <p class="card-category text-muted">Current Retail</p>
                        <h3 class="card-title">${{ "%.2f"|format(summary.total_retail) }}</h3>
                    </div>
                    <div class="icon">
                        <i class="fas fa-tag fa-2x text-info"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card card-stats">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <p class="card-category text-muted">Profit/Loss</p>
                        <h3 class="card-title {{ 'profit-positive' if summary.profit_loss >= 0 else 'profit-negative' }}">
                            ${{ "%.2f"|format(summary.profit_loss) }}
                        </h3>
                    </div>
                    <div class="icon">
                        <i class="fas fa-chart-line fa-2x {{ 'text-success' if summary.profit_loss >= 0 else 'text-danger' }}"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
            <i class="fas fa-list me-2"></i>Equipment Inventory
            {% if search_query %}
                <small class="text-muted">(Search: "{{ search_query }}")</small>
            {% endif %}
        </h5>
        <div class="d-flex gap-2">
            <form method="GET" action="{{ url_for('search') }}" class="d-flex search-box">
                <input type="text" name="q" class="form-control" placeholder="Search equipment..." 
                       value="{{ search_query or '' }}">
                <button type="submit" class="btn btn-outline-primary">
                    <i class="fas fa-search"></i>
                </button>
            </form>
            <a href="{{ url_for('export_csv') }}" class="btn btn-success" title="Export to CSV">
                <i class="fas fa-download me-1"></i>Export CSV
            </a>
            <a href="{{ url_for('add_equipment') }}" class="btn btn-primary">
                <i class="fas fa-plus me-1"></i>Add Equipment
            </a>
        </div>
    </div>
    <div class="card-body p-0">
        {% if equipment_list %}
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>ID</th>
                        <th>Description</th>
                        <th>Cost</th>
                        <th>Purchase Date</th>
                        <th>Current Retail</th>
                        <th>Current Resale</th>
                        <th>Location</th>
                        <th>Condition</th>
                        <th class="table-actions">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for equipment in equipment_list %}
                    <tr>
                        <td><span class="badge bg-secondary">{{ equipment.id }}</span></td>
                        <td>
                            <strong>{{ equipment.description }}</strong>
                            {% if equipment.date_added %}
                            <br><small class="text-muted">Added: {{ equipment.date_added[:10] }}</small>
                            {% endif %}
                        </td>
                        <td class="text-success">${{ "%.2f"|format(equipment.cost) }}</td>
                        <td>{{ equipment.purchase_date }}</td>
                        <td class="text-info">${{ "%.2f"|format(equipment.current_retail) }}</td>
                        <td class="text-warning">${{ "%.2f"|format(equipment.current_resale) }}</td>
                        <td>{{ equipment.resale_location or '-' }}</td>
                        <td>
                            <span class="badge 
                                {% if equipment.condition == 'Excellent' %}bg-success
                                {% elif equipment.condition == 'Good' %}bg-primary
                                {% elif equipment.condition == 'Fair' %}bg-warning
                                {% else %}bg-danger{% endif %}">
                                {{ equipment.condition }}
                            </span>
                        </td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <a href="{{ url_for('edit_equipment', equipment_id=equipment.id) }}" 
                                   class="btn btn-outline-primary" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </a>
                                <a href="{{ url_for('delete_equipment', equipment_id=equipment.id) }}" 
                                   class="btn btn-outline-danger" title="Delete"
                                   onclick="return confirm('Are you sure you want to delete this equipment?')">
                                    <i class="fas fa-trash"></i>
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="text-center py-5">
            <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
            <h5 class="text-muted">No equipment found</h5>
            <p class="text-muted">
                {% if search_query %}
                    No equipment matches your search criteria.
                    <a href="{{ url_for('index') }}">Show all equipment</a>
                {% else %}
                    Start by adding your first piece of equipment.
                {% endif %}
            </p>
            {% if not search_query %}
            <a href="{{ url_for('add_equipment') }}" class="btn btn-primary">
                <i class="fas fa-plus me-1"></i>Add First Equipment
            </a>
            {% endif %}
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}''')
    
    # Create add template
    with open('templates/add.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Add Equipment - Equipment Tracker{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-plus me-2"></i>Add New Equipment
                </h5>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-8 mb-3">
                            <label for="description" class="form-label">Description *</label>
                            <input type="text" class="form-control" id="description" name="description" 
                                   placeholder="Enter equipment description" required>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label for="cost" class="form-label">Purchase Cost *</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="cost" name="cost" 
                                       step="0.01" min="0" placeholder="0.00" required>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="purchase_date" class="form-label">Purchase Date</label>
                            <input type="date" class="form-control" id="purchase_date" name="purchase_date">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="condition" class="form-label">Condition</label>
                            <select class="form-select" id="condition" name="condition">
                                <option value="Excellent">Excellent</option>
                                <option value="Good" selected>Good</option>
                                <option value="Fair">Fair</option>
                                <option value="Poor">Poor</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="current_retail" class="form-label">Current Retail Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="current_retail" name="current_retail" 
                                       step="0.01" min="0" placeholder="0.00">
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="current_resale" class="form-label">Current Resale Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="current_resale" name="current_resale" 
                                       step="0.01" min="0" placeholder="0.00">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="resale_location" class="form-label">Resale Location</label>
                        <input type="text" class="form-control" id="resale_location" name="resale_location" 
                               placeholder="e.g., eBay, Craigslist, Local store">
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-1"></i>Add Equipment
                        </button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">
                            <i class="fas fa-times me-1"></i>Cancel
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
// Set today's date as default
document.getElementById('purchase_date').valueAsDate = new Date();
</script>
{% endblock %}''')
    
    # Create edit template
    with open('templates/edit.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Edit Equipment - Equipment Tracker{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-lg-8">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-edit me-2"></i>Edit Equipment
                </h5>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-8 mb-3">
                            <label for="description" class="form-label">Description *</label>
                            <input type="text" class="form-control" id="description" name="description" 
                                   value="{{ equipment.description }}" required>
                        </div>
                        <div class="col-md-4 mb-3">
                            <label for="cost" class="form-label">Purchase Cost *</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="cost" name="cost" 
                                       step="0.01" min="0" value="{{ equipment.cost }}" required>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="purchase_date" class="form-label">Purchase Date</label>
                            <input type="date" class="form-control" id="purchase_date" name="purchase_date" 
                                   value="{{ equipment.purchase_date }}">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="condition" class="form-label">Condition</label>
                            <select class="form-select" id="condition" name="condition">
                                <option value="Excellent" {{ 'selected' if equipment.condition == 'Excellent' else '' }}>Excellent</option>
                                <option value="Good" {{ 'selected' if equipment.condition == 'Good' else '' }}>Good</option>
                                <option value="Fair" {{ 'selected' if equipment.condition == 'Fair' else '' }}>Fair</option>
                                <option value="Poor" {{ 'selected' if equipment.condition == 'Poor' else '' }}>Poor</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="current_retail" class="form-label">Current Retail Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="current_retail" name="current_retail" 
                                       step="0.01" min="0" value="{{ equipment.current_retail }}">
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="current_resale" class="form-label">Current Resale Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="current_resale" name="current_resale" 
                                       step="0.01" min="0" value="{{ equipment.current_resale }}">
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="resale_location" class="form-label">Resale Location</label>
                        <input type="text" class="form-control" id="resale_location" name="resale_location" 
                               value="{{ equipment.resale_location }}" placeholder="e.g., eBay, Craigslist, Local store">
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-1"></i>Update Equipment
                        </button>
                        <a href="{{ url_for('index') }}" class="btn btn-secondary">
                            <i class="fas fa-times me-1"></i>Cancel
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')
    
    print("Equipment Tracker Web Application")
    print("=" * 40)
    print("Templates created successfully!")
    print("\nTo run the application:")
    print("1. Install Flask: pip install flask")
    print("2. Run: python app.py")
    print("3. Open: http://localhost:5000")
    print("\nStarting development server...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    