# 📊 Complete Guide: All Ways to Display Churn Prediction Data

This guide shows every possible way to display churn prediction data using your enhanced Company model methods.

## 🎯 **1. BASIC COUNTER CARDS**

### Risk Level Counters
```html
<!-- High Risk Counter -->
<div class="card border-left-danger shadow h-100">
    <div class="card-body">
        <div class="row no-gutters align-items-center">
            <div class="col mr-2">
                <div class="text-xs font-weight-bold text-danger text-uppercase mb-1">
                    High Risk Customers
                </div>
                <div class="h5 mb-0 font-weight-bold text-gray-800">
                    {{ company.get_high_risk_customer_count() }}
                </div>
                <small class="text-danger">
                    <i class="fas fa-exclamation-triangle me-1"></i>Needs immediate attention
                </small>
            </div>
            <div class="col-auto">
                <i class="fas fa-exclamation-triangle fa-2x text-gray-300"></i>
            </div>
        </div>
    </div>
</div>

<!-- Medium Risk Counter -->
<div class="card border-left-warning shadow h-100">
    <div class="card-body">
        <div class="row no-gutters align-items-center">
            <div class="col mr-2">
                <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                    Medium Risk
                </div>
                <div class="h5 mb-0 font-weight-bold text-gray-800">
                    {{ company.get_medium_risk_customer_count() }}
                </div>
                <small class="text-warning">
                    <i class="fas fa-eye me-1"></i>Monitor closely
                </small>
            </div>
            <div class="col-auto">
                <i class="fas fa-eye fa-2x text-gray-300"></i>
            </div>
        </div>
    </div>
</div>

<!-- Low Risk Counter -->
<div class="card border-left-success shadow h-100">
    <div class="card-body">
        <div class="row no-gutters align-items-center">
            <div class="col mr-2">
                <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                    Low Risk
                </div>
                <div class="h5 mb-0 font-weight-bold text-gray-800">
                    {{ company.get_low_risk_customer_count() }}
                </div>
                <small class="text-success">
                    <i class="fas fa-check me-1"></i>Stable customers
                </small>
            </div>
            <div class="col-auto">
                <i class="fas fa-check-circle fa-2x text-gray-300"></i>
            </div>
        </div>
    </div>
</div>
```

### Statistical Overview Cards
```html
<!-- Total Predictions -->
<div class="card border-left-info shadow h-100">
    <div class="card-body">
        <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
            Total Predictions
        </div>
        <div class="h5 mb-0 font-weight-bold">
            {{ company.get_prediction_count() }}
        </div>
    </div>
</div>

<!-- Average Churn Score -->
{% set churn_data = company.get_churn_overview() %}
<div class="card border-left-primary shadow h-100">
    <div class="card-body">
        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
            Average Risk Score
        </div>
        <div class="h5 mb-0 font-weight-bold">
            {{ "%.1f"|format(churn_data.avg_risk_score * 100) }}%
        </div>
        <div class="progress progress-sm">
            <div class="progress-bar bg-primary" role="progressbar" 
                 style="width: {{ churn_data.avg_risk_score * 100 }}%"></div>
        </div>
    </div>
</div>

<!-- Model Accuracy -->
{% set accuracy_data = company.get_prediction_accuracy_metrics() %}
<div class="card border-left-success shadow h-100">
    <div class="card-body">
        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
            Model Accuracy
        </div>
        <div class="h5 mb-0 font-weight-bold">
            {{ "%.1f"|format(accuracy_data.overall_accuracy * 100) }}%
        </div>
    </div>
</div>
```

## 📈 **2. PROGRESS BARS & INDICATORS**

### Simple Progress Bars
```html
{% set churn_viz = company.get_churn_visualization_data() %}

<!-- Health Score Progress Bar -->
<div class="mb-3">
    <div class="d-flex justify-content-between mb-1">
        <span class="text-sm font-weight-bold">Customer Health Score</span>
        <span class="text-sm">{{ "%.1f"|format(churn_viz.avg_churn_score * 100) }}%</span>
    </div>
    <div class="progress">
        <div class="progress-bar bg-success" role="progressbar" 
             style="width: {{ churn_viz.avg_churn_score * 100 }}%"
             aria-valuenow="{{ churn_viz.avg_churn_score * 100 }}" 
             aria-valuemin="0" aria-valuemax="100"></div>
    </div>
</div>

<!-- Risk Level Progress Bar -->
<div class="mb-3">
    <div class="d-flex justify-content-between mb-1">
        <span class="text-sm font-weight-bold">Risk Level</span>
        <span class="text-sm">{{ "%.1f"|format((1 - churn_viz.avg_churn_score) * 100) }}%</span>
    </div>
    <div class="progress">
        <div class="progress-bar bg-warning" role="progressbar" 
             style="width: {{ (1 - churn_viz.avg_churn_score) * 100 }}%"></div>
    </div>
</div>
```

### Multi-Level Progress Bars
```html
{% set risk_dist = company.get_risk_distribution() %}
{% set total = risk_dist.data[0] + risk_dist.data[1] + risk_dist.data[2] %}

<div class="mb-3">
    <h6>Customer Risk Distribution</h6>
    <div class="progress" style="height: 25px;">
        {% if total > 0 %}
        <div class="progress-bar bg-danger" role="progressbar" 
             style="width: {{ (risk_dist.data[0] / total) * 100 }}%"
             title="High Risk: {{ risk_dist.data[0] }} customers">
            {{ risk_dist.data[0] }}
        </div>
        <div class="progress-bar bg-warning" role="progressbar" 
             style="width: {{ (risk_dist.data[1] / total) * 100 }}%"
             title="Medium Risk: {{ risk_dist.data[1] }} customers">
            {{ risk_dist.data[1] }}
        </div>
        <div class="progress-bar bg-success" role="progressbar" 
             style="width: {{ (risk_dist.data[2] / total) * 100 }}%"
             title="Low Risk: {{ risk_dist.data[2] }} customers">
            {{ risk_dist.data[2] }}
        </div>
        {% endif %}
    </div>
    <div class="d-flex justify-content-between mt-1">
        <small class="text-danger">High Risk</small>
        <small class="text-warning">Medium Risk</small>
        <small class="text-success">Low Risk</small>
    </div>
</div>
```

### Circular Progress Rings (SVG)
```html
<style>
.progress-ring {
    transform: rotate(-90deg);
}
.progress-ring__circle {
    transition: stroke-dasharray 0.35s;
}
</style>

{% set gauge_data = company.get_gauge_chart_data() %}

<!-- Health Score Ring -->
<div class="text-center">
    <h6>Customer Health</h6>
    <svg class="progress-ring" width="120" height="120">
        <circle class="progress-ring__circle" stroke="#e9ecef" stroke-width="8" 
                fill="transparent" r="52" cx="60" cy="60"/>
        <circle class="progress-ring__circle" stroke="#28a745" stroke-width="8" 
                fill="transparent" r="52" cx="60" cy="60"
                style="stroke-dasharray: {{ gauge_data.overall_health }} 100"/>
    </svg>
    <div class="mt-2">
        <strong>{{ gauge_data.overall_health }}%</strong>
    </div>
</div>

<!-- Risk Level Ring -->
<div class="text-center">
    <h6>Risk Level</h6>
    <svg class="progress-ring" width="120" height="120">
        <circle class="progress-ring__circle" stroke="#e9ecef" stroke-width="8" 
                fill="transparent" r="52" cx="60" cy="60"/>
        <circle class="progress-ring__circle" stroke="#dc3545" stroke-width="8" 
                fill="transparent" r="52" cx="60" cy="60"
                style="stroke-dasharray: {{ gauge_data.churn_risk_level }} 100"/>
    </svg>
    <div class="mt-2">
        <strong>{{ gauge_data.churn_risk_level }}%</strong>
    </div>
</div>
```

## 🎨 **3. BADGES & PILLS**

### Risk Level Badges
```html
{% set top_customers = company.get_top_risk_customers(5) %}

<div class="list-group">
    {% for customer in top_customers.customers %}
    <div class="list-group-item d-flex justify-content-between align-items-center">
        <div>
            <strong>{{ customer.name }}</strong>
            <br><small class="text-muted">{{ customer.email }}</small>
        </div>
        <div>
            {% if customer.churn_probability > 0.7 %}
                <span class="badge bg-danger badge-pill">
                    High Risk - {{ "%.1f"|format(customer.churn_probability * 100) }}%
                </span>
            {% elif customer.churn_probability > 0.4 %}
                <span class="badge bg-warning badge-pill">
                    Medium Risk - {{ "%.1f"|format(customer.churn_probability * 100) }}%
                </span>
            {% else %}
                <span class="badge bg-success badge-pill">
                    Low Risk - {{ "%.1f"|format(customer.churn_probability * 100) }}%
                </span>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

### Status Pills with Icons
```html
<!-- Intervention Status Pills -->
{% set interventions = company.get_intervention_opportunities() %}

<div class="d-flex flex-wrap gap-2 mb-3">
    <span class="badge bg-danger rounded-pill">
        <i class="fas fa-exclamation-triangle me-1"></i>
        Immediate Action: {{ interventions.immediate_action|length }}
    </span>
    <span class="badge bg-warning rounded-pill">
        <i class="fas fa-eye me-1"></i>
        Watch List: {{ interventions.watch_list|length }}
    </span>
    <span class="badge bg-info rounded-pill">
        <i class="fas fa-calendar me-1"></i>
        Follow-up: {{ interventions.follow_up|length }}
    </span>
</div>
```

## 📊 **4. CHART VISUALIZATIONS**

### Doughnut Chart (Chart.js)
```html
<div class="card">
    <div class="card-header">
        <h6>Risk Distribution</h6>
    </div>
    <div class="card-body">
        <canvas id="riskDoughnutChart" height="300"></canvas>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('riskDoughnutChart').getContext('2d');
    
    // Get data from model
    const riskData = {{ company.get_risk_distribution() | tojson }};
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: riskData.labels,
            datasets: [{
                data: riskData.data,
                backgroundColor: riskData.colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
});
</script>
```

### Line Chart - Trend Analysis
```html
<div class="card">
    <div class="card-header">
        <h6>30-Day Churn Risk Trend</h6>
    </div>
    <div class="card-body">
        <canvas id="trendLineChart" height="300"></canvas>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('trendLineChart').getContext('2d');
    
    // Get trend data from model
    const trendData = {{ company.get_churn_trend_analysis(30) | tojson }};
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.dates,
            datasets: [{
                label: 'High Risk',
                data: trendData.high_risk_trend,
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                tension: 0.4
            }, {
                label: 'Medium Risk',
                data: trendData.medium_risk_trend,
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.4
            }, {
                label: 'Low Risk',
                data: trendData.low_risk_trend,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Customers'
                    }
                }
            }
        }
    });
});
</script>
```

### Bar Chart - Segment Analysis
```html
<div class="card">
    <div class="card-header">
        <h6>Risk by Customer Segment</h6>
    </div>
    <div class="card-body">
        <canvas id="segmentBarChart" height="300"></canvas>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('segmentBarChart').getContext('2d');
    
    // Get segment data from model
    const segmentData = {{ company.get_customer_segment_analysis() | tojson }};
    
    const labels = segmentData.segments.map(s => s.name);
    const highRisk = segmentData.segments.map(s => s.high_risk_count);
    const mediumRisk = segmentData.segments.map(s => s.medium_risk_count);
    const lowRisk = segmentData.segments.map(s => s.low_risk_count);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'High Risk',
                data: highRisk,
                backgroundColor: '#dc3545'
            }, {
                label: 'Medium Risk',
                data: mediumRisk,
                backgroundColor: '#ffc107'
            }, {
                label: 'Low Risk',
                data: lowRisk,
                backgroundColor: '#28a745'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { 
                    stacked: true,
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Customers'
                    }
                }
            }
        }
    });
});
</script>
```

### Scatter Plot - Value vs Risk
```html
<div class="card">
    <div class="card-header">
        <h6>Customer Value vs Churn Risk</h6>
    </div>
    <div class="card-body">
        <canvas id="valueRiskScatter" height="400"></canvas>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('valueRiskScatter').getContext('2d');
    
    // Get scatter data from model
    const scatterData = {{ company.get_scatter_plot_data() | tojson }};
    
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Customers',
                data: scatterData.customer_value_vs_risk,
                backgroundColor: function(context) {
                    const point = context.raw;
                    return point.y > 70 ? '#dc3545' : point.y > 40 ? '#ffc107' : '#28a745';
                },
                borderColor: '#fff',
                borderWidth: 2,
                pointRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Customer Value ($)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Churn Risk (%)'
                    },
                    min: 0,
                    max: 100
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return `${point.label}: $${point.x.toLocaleString()}, ${point.y}% risk`;
                        }
                    }
                }
            }
        }
    });
});
</script>
```

## 🌡️ **5. GAUGE CHARTS**

### Speedometer-Style Gauge
```html
<div class="card text-center">
    <div class="card-header">
        <h6>Customer Health Gauge</h6>
    </div>
    <div class="card-body">
        <canvas id="healthGauge" width="200" height="200"></canvas>
        <div class="mt-3">
            <h4 class="text-success">{{ company.get_gauge_chart_data().overall_health }}%</h4>
            <small class="text-muted">Overall Health Score</small>
        </div>
    </div>
</div>

<script>
function createGaugeChart(canvasId, value, maxValue = 100) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const color = value > 70 ? '#28a745' : value > 40 ? '#ffc107' : '#dc3545';
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [value, maxValue - value],
                backgroundColor: [color, '#e9ecef'],
                borderWidth: 0,
                cutout: '75%',
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        },
        plugins: [{
            beforeDraw: function(chart) {
                const { width, height, ctx } = chart;
                ctx.restore();
                
                const fontSize = (height / 100).toFixed(2);
                ctx.font = `bold ${fontSize}em Arial`;
                ctx.textBaseline = "middle";
                ctx.fillStyle = color;
                
                const text = value.toFixed(1) + "%";
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height / 1.4;
                
                ctx.fillText(text, textX, textY);
                ctx.save();
            }
        }]
    });
}

// Initialize gauge
document.addEventListener('DOMContentLoaded', function() {
    const gaugeData = {{ company.get_gauge_chart_data() | tojson }};
    createGaugeChart('healthGauge', gaugeData.overall_health);
});
</script>
```

## 📋 **6. TABLE DISPLAYS**

### Risk Assessment Table
```html
<div class="card">
    <div class="card-header">
        <h6>High-Risk Customers</h6>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Email</th>
                        <th>Risk Score</th>
                        <th>Value</th>
                        <th>Last Contact</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% set top_customers = company.get_top_risk_customers(10) %}
                    {% for customer in top_customers.customers %}
                    <tr>
                        <td>
                            <strong>{{ customer.name }}</strong>
                        </td>
                        <td>{{ customer.email }}</td>
                        <td>
                            <div class="d-flex align-items-center">
                                <div class="progress flex-grow-1 me-2" style="height: 8px;">
                                    <div class="progress-bar 
                                        {% if customer.churn_probability > 0.7 %}bg-danger
                                        {% elif customer.churn_probability > 0.4 %}bg-warning
                                        {% else %}bg-success{% endif %}" 
                                        style="width: {{ customer.churn_probability * 100 }}%"></div>
                                </div>
                                <small>{{ "%.1f"|format(customer.churn_probability * 100) }}%</small>
                            </div>
                        </td>
                        <td>${{ "{:,}"|format(customer.customer_value) }}</td>
                        <td>{{ customer.last_contact_date }}</td>
                        <td>
                            {% if customer.churn_probability > 0.7 %}
                                <button class="btn btn-danger btn-sm">Contact Now</button>
                            {% elif customer.churn_probability > 0.4 %}
                                <button class="btn btn-warning btn-sm">Schedule Call</button>
                            {% else %}
                                <button class="btn btn-success btn-sm">Monitor</button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

### Segment Analysis Table
```html
<div class="card">
    <div class="card-header">
        <h6>Risk by Customer Segment</h6>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>Segment</th>
                        <th>Total Customers</th>
                        <th>Avg Risk Score</th>
                        <th>High Risk</th>
                        <th>Medium Risk</th>
                        <th>Low Risk</th>
                        <th>Risk Distribution</th>
                    </tr>
                </thead>
                <tbody>
                    {% set segment_data = company.get_customer_segment_analysis() %}
                    {% for segment in segment_data.segments %}
                    <tr>
                        <td><strong>{{ segment.name }}</strong></td>
                        <td>{{ segment.count }}</td>
                        <td>
                            <span class="badge 
                                {% if segment.avg_risk > 0.6 %}bg-danger
                                {% elif segment.avg_risk > 0.3 %}bg-warning
                                {% else %}bg-success{% endif %}">
                                {{ "%.1f"|format(segment.avg_risk * 100) }}%
                            </span>
                        </td>
                        <td>{{ segment.high_risk_count }}</td>
                        <td>{{ segment.medium_risk_count }}</td>
                        <td>{{ segment.low_risk_count }}</td>
                        <td>
                            {% if segment.count > 0 %}
                            <div class="progress" style="height: 20px;">
                                <div class="progress-bar bg-danger" 
                                     style="width: {{ (segment.high_risk_count / segment.count) * 100 }}%"
                                     title="High Risk: {{ segment.high_risk_count }}"></div>
                                <div class="progress-bar bg-warning" 
                                     style="width: {{ (segment.medium_risk_count / segment.count) * 100 }}%"
                                     title="Medium Risk: {{ segment.medium_risk_count }}"></div>
                                <div class="progress-bar bg-success" 
                                     style="width: {{ (segment.low_risk_count / segment.count) * 100 }}%"
                                     title="Low Risk: {{ segment.low_risk_count }}"></div>
                            </div>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

## 📅 **7. TIMELINE DISPLAYS**

### Customer Journey Timeline
```html
<style>
.timeline {
    position: relative;
    padding-left: 30px;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 15px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e9ecef;
}

.timeline-item {
    position: relative;
    margin-bottom: 30px;
    padding-left: 30px;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -8px;
    top: 5px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #007bff;
    border: 2px solid #fff;
    box-shadow: 0 0 0 2px #e9ecef;
}

.timeline-item.high-risk::before { background: #dc3545; }
.timeline-item.medium-risk::before { background: #ffc107; }
.timeline-item.low-risk::before { background: #28a745; }
</style>

<div class="card">
    <div class="card-header">
        <h6>Recent Customer Events</h6>
    </div>
    <div class="card-body">
        <div class="timeline">
            {% set timeline_data = company.get_timeline_data() %}
            {% for event in timeline_data.events %}
            <div class="timeline-item {{ event.risk_level }}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">{{ event.customer_name }}</h6>
                        <p class="mb-2">{{ event.description }}</p>
                        <small class="text-muted">{{ event.date }}</small>
                    </div>
                    <span class="badge bg-{{ 'danger' if event.risk_level == 'high' else 'warning' if event.risk_level == 'medium' else 'success' }}">
                        {{ event.risk_score }}% risk
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

## 🚨 **8. ALERT DISPLAYS**

### Risk Alerts
```html
{% set interventions = company.get_intervention_opportunities() %}

<!-- Immediate Action Alert -->
{% if interventions.immediate_action|length > 0 %}
<div class="alert alert-danger d-flex align-items-center" role="alert">
    <i class="fas fa-exclamation-triangle fa-lg me-3"></i>
    <div>
        <strong>Urgent Action Required!</strong>
        {{ interventions.immediate_action|length }} customers need immediate attention.
        <a href="#" class="alert-link">Take action now</a>.
    </div>
</div>
{% endif %}

<!-- Watch List Alert -->
{% if interventions.watch_list|length > 0 %}
<div class="alert alert-warning d-flex align-items-center" role="alert">
    <i class="fas fa-eye fa-lg me-3"></i>
    <div>
        <strong>Monitor Closely:</strong>
        {{ interventions.watch_list|length }} customers on watch list.
        <a href="#" class="alert-link">Review list</a>.
    </div>
</div>
{% endif %}

<!-- Success Alert -->
{% set churn_viz = company.get_churn_visualization_data() %}
{% if churn_viz.avg_churn_score < 0.3 %}
<div class="alert alert-success d-flex align-items-center" role="alert">
    <i class="fas fa-check-circle fa-lg me-3"></i>
    <div>
        <strong>Great News!</strong>
        Your customer base is showing low churn risk ({{ "%.1f"|format(churn_viz.avg_churn_score * 100) }}% average).
    </div>
</div>
{% endif %}
```

### Notification Banners
```html
{% set churn_overview = company.get_churn_overview() %}

<div class="row mb-4">
    <div class="col-12">
        {% if churn_overview.trend_percentage > 10 %}
        <div class="alert alert-danger border-left-danger">
            <div class="d-flex">
                <div class="alert-icon">
                    <i class="fas fa-arrow-up text-danger"></i>
                </div>
                <div>
                    <h6 class="alert-heading">Churn Risk Increasing</h6>
                    <p class="mb-0">
                        Risk levels have increased by {{ "%.1f"|format(churn_overview.trend_percentage) }}% 
                        compared to last period. Consider reviewing your retention strategies.
                    </p>
                </div>
            </div>
        </div>
        {% elif churn_overview.trend_percentage < -5 %}
        <div class="alert alert-success border-left-success">
            <div class="d-flex">
                <div class="alert-icon">
                    <i class="fas fa-arrow-down text-success"></i>
                </div>
                <div>
                    <h6 class="alert-heading">Improvement Detected</h6>
                    <p class="mb-0">
                        Great work! Risk levels have decreased by {{ "%.1f"|format(abs(churn_overview.trend_percentage)) }}% 
                        compared to last period.
                    </p>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
```

## 🎯 **9. HEATMAP DISPLAYS**

### Risk Heatmap Grid
```html
<style>
.heatmap-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 2px;
    background: #f8f9fa;
    padding: 10px;
    border-radius: 8px;
}

.heatmap-cell {
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    border-radius: 4px;
    text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
}

.risk-very-low { background-color: #28a745; }
.risk-low { background-color: #6c757d; }
.risk-medium { background-color: #ffc107; color: #000; }
.risk-high { background-color: #fd7e14; }
.risk-very-high { background-color: #dc3545; }
</style>

<div class="card">
    <div class="card-header">
        <h6>Risk Heatmap by Segment & Time</h6>
    </div>
    <div class="card-body">
        {% set heatmap_data = company.get_heatmap_data() %}
        <div class="heatmap-grid">
            {% for i in range(heatmap_data.risk_matrix|length) %}
                {% for j in range(heatmap_data.risk_matrix[i]|length) %}
                    {% set risk_value = heatmap_data.risk_matrix[i][j] %}
                    {% set risk_class = 'risk-very-low' if risk_value < 20 else 
                                       'risk-low' if risk_value < 35 else 
                                       'risk-medium' if risk_value < 50 else 
                                       'risk-high' if risk_value < 70 else 
                                       'risk-very-high' %}
                    <div class="heatmap-cell {{ risk_class }}" 
                         title="{{ heatmap_data.customer_segments[i] }} - {{ heatmap_data.time_periods[j] }}: {{ risk_value }}%">
                        {{ risk_value }}%
                    </div>
                {% endfor %}
            {% endfor %}
        </div>
        
        <!-- Legend -->
        <div class="d-flex justify-content-center mt-3">
            <div class="d-flex align-items-center">
                <span class="badge risk-very-low me-2">Very Low</span>
                <span class="badge risk-low me-2">Low</span>
                <span class="badge risk-medium me-2">Medium</span>
                <span class="badge risk-high me-2">High</span>
                <span class="badge risk-very-high">Very High</span>
            </div>
        </div>
    </div>
</div>
```

## 📊 **10. DASHBOARD WIDGETS**

### Compact Summary Widget
```html
<div class="card bg-gradient-primary text-white">
    <div class="card-body">
        <div class="row">
            <div class="col">
                <h5 class="card-title">Churn Risk Summary</h5>
                {% set churn_overview = company.get_churn_overview() %}
                <div class="row text-center">
                    <div class="col-4">
                        <div class="h4 mb-0">{{ churn_overview.high_risk_count }}</div>
                        <small>High Risk</small>
                    </div>
                    <div class="col-4">
                        <div class="h4 mb-0">{{ churn_overview.medium_risk_count }}</div>
                        <small>Medium Risk</small>
                    </div>
                    <div class="col-4">
                        <div class="h4 mb-0">{{ churn_overview.low_risk_count }}</div>
                        <small>Low Risk</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Mini Gauge Widget
```html
<div class="card text-center">
    <div class="card-body py-4">
        <div class="d-inline-block position-relative">
            <canvas id="miniGauge" width="80" height="80"></canvas>
        </div>
        <h6 class="mt-2 mb-0">Health Score</h6>
        <small class="text-muted">{{ company.get_gauge_chart_data().overall_health }}%</small>
    </div>
</div>
```

### Action Required Widget
```html
{% set interventions = company.get_intervention_opportunities() %}

<div class="card border-left-danger">
    <div class="card-body">
        <div class="d-flex justify-content-between">
            <div>
                <h6 class="text-danger mb-2">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    Actions Required
                </h6>
                <div class="row text-center">
                    <div class="col">
                        <div class="h5 text-danger mb-0">{{ interventions.immediate_action|length }}</div>
                        <small>Urgent</small>
                    </div>
                    <div class="col">
                        <div class="h5 text-warning mb-0">{{ interventions.watch_list|length }}</div>
                        <small>Monitor</small>
                    </div>
                    <div class="col">
                        <div class="h5 text-info mb-0">{{ interventions.follow_up|length }}</div>
                        <small>Follow-up</small>
                    </div>
                </div>
            </div>
            <div class="align-self-center">
                <i class="fas fa-tasks fa-2x text-gray-300"></i>
            </div>
        </div>
    </div>
</div>
```

## 🎨 **11. CUSTOM PREDICTION METERS**

### Risk Assessment Meter
```html
<style>
.prediction-meter {
    background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
    height: 20px;
    border-radius: 10px;
    position: relative;
    margin: 10px 0;
}

.prediction-indicator {
    position: absolute;
    top: -5px;
    width: 30px;
    height: 30px;
    background: white;
    border: 3px solid #333;
    border-radius: 50%;
    transform: translateX(-50%);
}
</style>

{% set top_customers = company.get_top_risk_customers(5) %}

<div class="card">
    <div class="card-header">
        <h6>Customer Risk Assessment</h6>
    </div>
    <div class="card-body">
        {% for customer in top_customers.customers %}
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <strong>{{ customer.name }}</strong>
                <span class="badge bg-{{ 'danger' if customer.churn_probability > 0.7 else 'warning' if customer.churn_probability > 0.4 else 'success' }}">
                    {{ "%.1f"|format(customer.churn_probability * 100) }}%
                </span>
            </div>
            <div class="prediction-meter">
                <div class="prediction-indicator" 
                     style="left: {{ customer.churn_probability * 100 }}%;"></div>
            </div>
            <div class="d-flex justify-content-between">
                <small class="text-success">Safe (0%)</small>
                <small class="text-danger">High Risk (100%)</small>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

## 📱 **12. MOBILE-FRIENDLY DISPLAYS**

### Mobile Cards
```html
<div class="d-md-none"> <!-- Show only on mobile -->
    {% set churn_overview = company.get_churn_overview() %}
    
    <!-- Mobile Risk Summary -->
    <div class="card mb-3">
        <div class="card-body text-center">
            <h6 class="card-title">Risk Summary</h6>
            <div class="row">
                <div class="col-4">
                    <div class="text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x"></i>
                        <div class="h6 mt-1">{{ churn_overview.high_risk_count }}</div>
                        <small>High Risk</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="text-warning">
                        <i class="fas fa-eye fa-2x"></i>
                        <div class="h6 mt-1">{{ churn_overview.medium_risk_count }}</div>
                        <small>Medium</small>
                    </div>
                </div>
                <div class="col-4">
                    <div class="text-success">
                        <i class="fas fa-check fa-2x"></i>
                        <div class="h6 mt-1">{{ churn_overview.low_risk_count }}</div>
                        <small>Low Risk</small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Swipeable Customer Cards
```html
<div class="d-md-none"> <!-- Mobile only -->
    <div class="card">
        <div class="card-header">
            <h6>High-Risk Customers <small class="text-muted">(Swipe to see more)</small></h6>
        </div>
        <div class="card-body p-0">
            <div class="overflow-auto" style="white-space: nowrap;">
                {% set top_customers = company.get_top_risk_customers(10) %}
                {% for customer in top_customers.customers %}
                <div class="card d-inline-block m-2" style="width: 250px; white-space: normal;">
                    <div class="card-body">
                        <h6 class="card-title">{{ customer.name }}</h6>
                        <p class="card-text small">{{ customer.email }}</p>
                        <div class="progress mb-2" style="height: 8px;">
                            <div class="progress-bar bg-{{ 'danger' if customer.churn_probability > 0.7 else 'warning' if customer.churn_probability > 0.4 else 'success' }}" 
                                 style="width: {{ customer.churn_probability * 100 }}%"></div>
                        </div>
                        <div class="d-flex justify-content-between">
                            <small>{{ "%.1f"|format(customer.churn_probability * 100) }}% risk</small>
                            <small>${{ "{:,}"|format(customer.customer_value) }}</small>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

## 🔄 **13. REAL-TIME UPDATES**

### Auto-Refreshing Widgets
```html
<div id="liveRiskCounter" class="card">
    <div class="card-body text-center">
        <h6>Live Risk Monitor</h6>
        <div class="h4 text-danger" id="highRiskCount">-</div>
        <small>High-Risk Customers</small>
        <div class="mt-2">
            <small class="text-muted">
                Last updated: <span id="lastUpdate">-</span>
            </small>
        </div>
    </div>
</div>

<script>
function updateRiskCounters() {
    fetch('/company/api/churn/overview')
        .then(response => response.json())
        .then(data => {
            document.getElementById('highRiskCount').textContent = data.high_risk_count;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        })
        .catch(error => console.error('Error updating risk counters:', error));
}

// Update every 5 minutes
setInterval(updateRiskCounters, 300000);

// Initial load
document.addEventListener('DOMContentLoaded', updateRiskCounters);
</script>
```

## 🎛️ **14. INTERACTIVE FILTERS**

### Risk Level Filter
```html
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h6>Customer List</h6>
            <div class="btn-group btn-group-sm" role="group">
                <input type="radio" class="btn-check" name="riskFilter" id="filterAll" value="all" checked>
                <label class="btn btn-outline-primary" for="filterAll">All</label>
                
                <input type="radio" class="btn-check" name="riskFilter" id="filterHigh" value="high">
                <label class="btn btn-outline-danger" for="filterHigh">High Risk</label>
                
                <input type="radio" class="btn-check" name="riskFilter" id="filterMedium" value="medium">
                <label class="btn btn-outline-warning" for="filterMedium">Medium</label>
                
                <input type="radio" class="btn-check" name="riskFilter" id="filterLow" value="low">
                <label class="btn btn-outline-success" for="filterLow">Low Risk</label>
            </div>
        </div>
    </div>
    <div class="card-body">
        <div id="customerList">
            <!-- Customer list populated by JavaScript -->
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('input[name="riskFilter"]');
    
    filterButtons.forEach(button => {
        button.addEventListener('change', function() {
            const filterValue = this.value;
            updateCustomerList(filterValue);
        });
    });
    
    function updateCustomerList(filter = 'all') {
        let url = '/company/api/churn/top-risk-customers?limit=20';
        if (filter !== 'all') {
            url += `&risk_level=${filter}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                displayCustomers(data.customers);
            })
            .catch(error => console.error('Error filtering customers:', error));
    }
    
    function displayCustomers(customers) {
        const listContainer = document.getElementById('customerList');
        listContainer.innerHTML = customers.map(customer => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${customer.name}</strong>
                    <br><small class="text-muted">${customer.email}</small>
                </div>
                <span class="badge bg-${customer.churn_probability > 0.7 ? 'danger' : customer.churn_probability > 0.4 ? 'warning' : 'success'}">
                    ${(customer.churn_probability * 100).toFixed(1)}%
                </span>
            </div>
        `).join('');
    }
    
    // Initial load
    updateCustomerList();
});
</script>
```

---

## 🎯 **Summary**

This comprehensive guide shows **14 different categories** of displaying churn prediction data:

1. **📊 Basic Counter Cards** - Simple risk level counts
2. **📈 Progress Bars & Indicators** - Visual progress displays
3. **🎨 Badges & Pills** - Status indicators
4. **📊 Chart Visualizations** - Professional charts
5. **🌡️ Gauge Charts** - Speedometer-style displays
6. **📋 Table Displays** - Detailed data tables
7. **📅 Timeline Displays** - Chronological events
8. **🚨 Alert Displays** - Warning and notification systems
9. **🎯 Heatmap Displays** - Risk intensity grids
10. **📊 Dashboard Widgets** - Compact summary displays
11. **🎨 Custom Prediction Meters** - Specialized risk meters
12. **📱 Mobile-Friendly Displays** - Responsive mobile layouts
13. **🔄 Real-Time Updates** - Live data refreshing
14. **🎛️ Interactive Filters** - Dynamic data filtering

Each method uses your enhanced Company model methods like:
- `company.get_churn_visualization_data()`
- `company.get_risk_distribution()`
- `company.get_top_risk_customers()`
- `company.get_intervention_opportunities()`

All examples are production-ready and can be implemented immediately with your enhanced model! 🚀