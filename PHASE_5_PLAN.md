# PHASE 5: ANALYTICS & MONITORING - DETAILED PLAN

**Status**: 🔄 IN PROGRESS  
**Date Started**: 2026-03-04 03:19 UTC  
**Estimated Duration**: 30-40 hours  
**Scope**: Complete analytics, dashboards, monitoring, and call insights

---

## PHASE 5 OVERVIEW

Build comprehensive analytics, monitoring, and insights platform for:
- Call metrics and statistics
- Agent performance tracking
- Cost analysis (OpenAI, ElevenLabs, Twilio)
- Real-time dashboards
- Alerts and notifications
- Historical reporting

---

## TASK BREAKDOWN (10 Tasks)

### TASK 5.1: Analytics Service Layer
**Estimated**: 2 hours | **Lines**: 300-400

**Purpose**: Core analytics calculations and aggregations

**Deliverables**:
- `backend/app/services/analytics_service.py`

**Features**:
```python
class AnalyticsService:
    # Call Metrics
    async def get_call_stats(company_id, date_range)
    async def get_call_success_rate(agent_id, date_range)
    async def get_average_call_duration(agent_id, date_range)
    async def get_calls_by_status(agent_id, date_range)
    
    # Agent Performance
    async def get_agent_metrics(agent_id, date_range)
    async def get_agent_ranking(company_id, metric, date_range)
    async def get_agent_satisfaction(agent_id, date_range)
    
    # Cost Analysis
    async def get_total_api_costs(company_id, date_range)
    async def get_cost_breakdown(company_id, date_range)
    async def get_cost_per_call(company_id, date_range)
    
    # Trends
    async def get_call_volume_trend(company_id, time_bucket)
    async def get_duration_trend(company_id, time_bucket)
    async def get_cost_trend(company_id, time_bucket)
```

**Integration**:
- Aggregate from Call, CallTranscript tables
- Use existing phone_number call_count
- Calculate ai_cost_usd per call

---

### TASK 5.2: Call Metrics Endpoints
**Estimated**: 2 hours | **Lines**: 250-350

**Purpose**: REST API for analytics queries

**Deliverables**:
- `backend/app/api/routes/analytics.py`

**Endpoints**:
```
GET  /api/v1/analytics/calls/summary
     - Overall call volume, success rate, avg duration
     - Company-level aggregation
     Response: { total_calls, successful_calls, success_rate, ... }

GET  /api/v1/analytics/calls/by-agent
     - Per-agent statistics
     Query: ?date_from=&date_to=&metric=duration
     Response: [{ agent_id, agent_name, calls, duration, ... }, ...]

GET  /api/v1/analytics/calls/by-phone
     - Per-phone-number statistics
     Query: ?date_from=&date_to=
     Response: [{ phone_number, calls, success_rate, ... }, ...]

GET  /api/v1/analytics/calls/trend
     - Call volume over time
     Query: ?bucket=day|week|month&date_from=&date_to=
     Response: [{ date, count, duration, cost }, ...]

GET  /api/v1/analytics/agents/performance
     - Agent rankings and metrics
     Query: ?sort=calls|duration|success_rate
     Response: [{ agent_id, name, rank, score, ... }, ...]

GET  /api/v1/analytics/costs/summary
     - Total costs by service
     Query: ?date_from=&date_to=
     Response: { total, openai, elevenlabs, twilio, breakdown }

GET  /api/v1/analytics/costs/per-call
     - Cost analysis by call
     Query: ?date_from=&date_to=&limit=100
     Response: [{ call_id, duration, agents, cost }, ...]

GET  /api/v1/analytics/health/uptime
     - Service availability and uptime
     Response: { uptime_percent, incidents, mttr }
```

**Security**:
- Company-level access control
- Agent-scoped filtering
- Date range validation

---

### TASK 5.3: Dashboard Frontend Component
**Estimated**: 3 hours | **Lines**: 800-1000

**Purpose**: Real-time analytics dashboard UI

**Deliverables**:
- `frontend/src/components/AnalyticsDashboard.jsx`
- `frontend/src/components/DashboardCard.jsx` (reusable)
- `frontend/src/components/MetricChart.jsx` (charts)
- `frontend/src/components/TrendChart.jsx` (trends)

**Features**:

**Dashboard Sections**:
1. **Summary Cards**
   - Total calls (today/week/month)
   - Success rate
   - Avg call duration
   - Total cost (today/week/month)

2. **Key Metrics**
   - Calls by status (pie chart)
   - Call duration distribution (histogram)
   - Calls by time of day (line chart)
   - Cost breakdown by service (pie chart)

3. **Agent Performance**
   - Agent rankings (table, sortable)
   - Calls per agent (bar chart)
   - Avg duration per agent (bar chart)
   - Success rate per agent (horizontal bar)

4. **Phone Performance**
   - Calls per phone number (bar chart)
   - Success rate per phone (table)
   - Most active numbers (top 10)

5. **Cost Analysis**
   - Cost trend over time (line chart)
   - Cost per call (scatter plot)
   - Service breakdown (stacked bar)
   - Projected monthly cost

6. **Time Filters**
   - Date range picker
   - Preset ranges (Today, Week, Month, Quarter, Year)
   - Auto-refresh toggle

7. **Export Options**
   - Download as CSV
   - Download as PDF
   - Email report

**Technology**:
- React for UI
- Recharts for charts/graphs
- Date picker library
- CSV/PDF export libs

---

### TASK 5.4: Real-time Monitoring Component
**Estimated**: 2 hours | **Lines**: 400-500

**Purpose**: Live monitoring of ongoing calls

**Deliverables**:
- `frontend/src/components/LiveMonitoring.jsx`

**Features**:
- **Active Calls Table**
  - Call ID, Caller, Agent, Duration, Status
  - Real-time updates via WebSocket
  - Call detail modal on click

- **Service Health**
  - Twilio status (green/yellow/red)
  - OpenAI status
  - ElevenLabs status
  - PostgreSQL status
  - Uptime indicators

- **System Stats**
  - Current active calls
  - API response time
  - Error rate (last 5 min)
  - Queue length (if applicable)

- **Alerts Panel**
  - Real-time alerts
  - Failed calls
  - API errors
  - Rate limiting warnings

**Technology**:
- WebSocket for real-time updates
- Redux for state management (or Context API)
- Live metrics polling

---

### TASK 5.5: Agent Performance Report
**Estimated**: 2 hours | **Lines**: 300-400

**Purpose**: Detailed agent metrics and rankings

**Deliverables**:
- `frontend/src/components/AgentReport.jsx`

**Features**:
- **Agent Selection**
  - Dropdown to select agent
  - View all agents

- **Performance Metrics**
  - Total calls handled
  - Avg call duration
  - Success rate
  - Customer satisfaction (if implemented)
  - Cost per call
  - Peak hours
  - Response time

- **Trends**
  - Calls over time (line chart)
  - Duration trend
  - Success rate trend
  - Quality trend (if scoring available)

- **Comparison**
  - vs company average
  - vs other agents (ranking)
  - vs previous period

- **Export**
  - Generate PDF report
  - Download data

---

### TASK 5.6: Cost Analysis Dashboard
**Estimated**: 2 hours | **Lines**: 350-450

**Purpose**: Financial tracking and optimization

**Deliverables**:
- `frontend/src/components/CostAnalytics.jsx`

**Features**:
- **Cost Summary**
  - Total spend (period)
  - Average cost per call
  - Projected monthly
  - Budget vs actual

- **Cost Breakdown**
  - By service (Twilio, OpenAI, ElevenLabs, etc.)
  - By agent
  - By phone number
  - By time period

- **Cost Trends**
  - Spending over time
  - Cost per call trend
  - Service cost comparison

- **Optimization Insights**
  - Most expensive agents
  - Most expensive phone numbers
  - Peak cost hours
  - Recommendations

- **Forecasting**
  - Projected monthly cost
  - Cost trajectory
  - Budget alerts

---

### TASK 5.7: Frontend Analytics Service
**Estimated**: 1 hour | **Lines**: 200-250

**Purpose**: API client for analytics endpoints

**Deliverables**:
- `frontend/src/services/analyticsService.js`

**Methods**:
```javascript
// Call metrics
getCallsSummary(dateRange)
getCallsByAgent(dateRange, filters)
getCallsByPhone(dateRange)
getCallTrends(bucket, dateRange)

// Agent performance
getAgentMetrics(agentId, dateRange)
getAgentRanking(metric, dateRange)

// Cost analysis
getCostsSummary(dateRange)
getCostBreakdown(dateRange)
getCostPerCall(dateRange)

// Health
getSystemHealth()
getUptime()

// Export
exportReport(format, data)
```

---

### TASK 5.8: Database Queries & Indexes
**Estimated**: 1 hour | **Lines**: 100-150

**Purpose**: Optimize analytics query performance

**Deliverables**:
- `backend/alembic/versions/003_add_analytics_indexes.py`

**Changes**:
- Index on Call.created_at (for date filtering)
- Index on Call.status (for status grouping)
- Index on Call.agent_id + Call.created_at (composite)
- Index on Call.duration_seconds (for sorting)
- Index on Call.ai_cost_usd (for cost queries)
- View: v_call_daily_stats (aggregated daily)
- View: v_agent_metrics (per-agent aggregation)

---

### TASK 5.9: Alerts & Notifications
**Estimated**: 2 hours | **Lines**: 250-350

**Purpose**: System alerts and notifications

**Deliverables**:
- `backend/app/services/alert_service.py`

**Features**:
```python
class AlertService:
    # Define alerts
    async def check_high_error_rate(company_id)
    async def check_api_failures(service_name)
    async def check_budget_exceeded(company_id)
    async def check_agent_offline(agent_id)
    async def check_queue_backlog(phone_id)
    
    # Send notifications
    async def send_alert(alert_type, severity, message)
    async def send_email_alert(user_email, subject, body)
    async def send_slack_alert(webhook_url, message)
```

**Alert Types**:
- High error rate (> 5%)
- API service down
- Budget exceeded
- Agent offline (no calls in 1h)
- Queue backlog (> 10 waiting)
- Cost spike

**Notification Channels**:
- In-app notifications
- Email
- Slack (if configured)
- SMS (optional)

---

### TASK 5.10: Documentation & Testing
**Estimated**: 2 hours | **Lines**: 500+

**Purpose**: Complete documentation and validation

**Deliverables**:
- `PHASE_5_SUMMARY.md` (detailed report)
- Unit tests for analytics_service
- Integration tests for endpoints
- Frontend component tests

**Coverage**:
- Analytics calculations (unit)
- API endpoints (integration)
- Dashboard rendering (UI)
- Export functionality
- Error handling

---

## TIMELINE & MILESTONES

```
Day 1 (3-4 hours):
  ✓ TASK 5.1: Analytics Service (2h)
  ✓ TASK 5.2: API Endpoints (2h)

Day 2 (4-5 hours):
  ✓ TASK 5.3: Dashboard Component (3h)
  ✓ TASK 5.4: Live Monitoring (2h)

Day 3 (3-4 hours):
  ✓ TASK 5.5: Agent Report (2h)
  ✓ TASK 5.6: Cost Analytics (2h)

Day 4 (2-3 hours):
  ✓ TASK 5.7: Frontend Service (1h)
  ✓ TASK 5.8: Database Indexes (1h)
  ✓ TASK 5.9: Alerts (2h)

Day 5 (2 hours):
  ✓ TASK 5.10: Documentation & Testing (2h)

TOTAL: 14-18 hours (estimated 30-40 with testing/refinement)
```

---

## SUCCESS CRITERIA

✅ Analytics Service: All calculations working  
✅ API Endpoints: All queries returning correct data  
✅ Dashboard: All charts rendering with live data  
✅ Performance: Dashboard loads < 2 seconds  
✅ Accuracy: Analytics match source data  
✅ Security: Company isolation verified  
✅ Documentation: Complete with examples  
✅ Tests: 80%+ coverage  

---

## STARTING NOW

Ready to begin TASK 5.1: Analytics Service Layer

