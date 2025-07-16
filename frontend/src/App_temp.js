
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8080';

const invokeAgent = async (userId, query) => {
  try {
    const response = await axios.post(`${API_URL}/agent/invoke`, {
      user_id: userId,
      query: query,
    });
    return response.data;
  } catch (error) {
    console.error(`Error invoking agent for query "${query}":`, error);
    throw error.response?.data?.details || 'An agent error occurred. Please try again.';
  }
};


// --- Login Component (Unchanged) ---
// This component's logic remains the same as it uses the separate /login endpoint.
const Login = ({ onLoginSuccess }) => {
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!userId) {
      setError('User ID cannot be empty.');
      return;
    }
    try {
      const response = await axios.post(`${API_URL}/login`, { user_id: userId });
      if (response.data.success) {
        onLoginSuccess(response.data.user);
      }
    } catch (err) {
      setError('Login failed. Please check the User ID.');
      console.error(err);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Leave Management System</h2>
        <p>Please enter your User ID to continue.</p>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            value={userId}
            onChange={(e) => {
              setUserId(e.target.value);
              setError('');
            }}
            placeholder="e.g., user001"
          />
          <button type="submit">Login</button>
          {error && <p className="error-message">{error}</p>}
        </form>
         <p className="login-hint">Hint: Try `user001`, `user002`, etc., up to `user010`.</p>
      </div>
    </div>
  );
};


// --- Dashboard Component (Refactored) ---
const Dashboard = ({ user, onLogout }) => {
  const [balances, setBalances] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [leaveType, setLeaveType] = useState('casual_leave');
  const [numberOfDays, setNumberOfDays] = useState(1);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [reason, setReason] = useState('');
  const [formMessage, setFormMessage] = useState({ type: '', text: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // --- Memoized function to fetch all dashboard data ---
  // useCallback prevents this function from being recreated on every render.
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Use Promise.all to fetch balance and history concurrently for better performance.
      const [balanceResult, historyResult] = await Promise.all([
        invokeAgent(user.id, "Get my current leave balance."),
        invokeAgent(user.id, "Get my entire leave history.")
      ]);

      // Process the results from the agent
      if (balanceResult?.balances) {
        setBalances(balanceResult.balances);
      }
      if (Array.isArray(historyResult?.requests)) {
        setHistory(historyResult.requests);
      } else {
        setHistory([]); // Ensure history is always an array
      }
    } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        setFormMessage({ type: 'error', text: 'Could not load dashboard data. Please refresh the page.' });
    } finally {
        setLoading(false);
    }
  }, [user.id]); // This function depends on user.id

  // --- Effect to fetch initial data when component mounts ---
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // --- Handler for submitting the leave application form ---
  const handleApplyLeave = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormMessage({ type: '', text: '' });
    
    // Construct a natural language query for the agent from the form data.
    const query = `Apply for ${leaveType.replace('_', ' ')} for ${numberOfDays} days, starting on ${startDate}. The reason is: ${reason}`;
    
    try {
        const result = await invokeAgent(user.id, query);
        
        if (result.success) {
            setFormMessage({ type: 'success', text: result.message || 'Leave applied successfully!' });
            // Reset form fields for the next application
            setLeaveType('casual_leave');
            setNumberOfDays(1);
            setReason('');
            // Refresh dashboard data to show the updated balance and history
            await fetchDashboardData();
        } else {
            // Handle cases where the agent returns a failure message (e.g., insufficient balance)
            setFormMessage({ type: 'error', text: `Failed to apply for leave. ${result.message || result.error || 'An unknown error occurred.'}` });
        }
    } catch (error) {
        setFormMessage({ type: 'error', text: `${error}` });
        console.error(error);
    } finally {
        setIsSubmitting(false);
    }
  };

  // --- Render Method ---
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Welcome, {user.name}!</h1>
        <button onClick={onLogout} className="logout-button">Logout</button>
      </header>
      <main className="dashboard-main">
        {/* Apply for Leave Card */}
        <div className="card">
          <h3>Apply for Leave</h3>
          <form onSubmit={handleApplyLeave} className="leave-form">
            <div className="form-group">
                <label>Leave Type</label>
                <select value={leaveType} onChange={e => setLeaveType(e.target.value)}>
                    <option value="casual_leave">Casual Leave</option>
                    <option value="sick_leave">Sick Leave</option>
                    <option value="earned_leave">Earned Leave</option>
                </select>
            </div>
            <div className="form-group">
                <label>Number of Days</label>
                <input type="number" min="1" value={numberOfDays} onChange={e => setNumberOfDays(e.target.value)} />
            </div>
            <div className="form-group">
                <label>Start Date</label>
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
            </div>
            <div className="form-group full-width">
                <label>Reason</label>
                <textarea value={reason} onChange={e => setReason(e.target.value)} required />
            </div>
            <button type="submit" className="full-width" disabled={isSubmitting}>
                {isSubmitting ? 'Submitting...' : 'Submit Request'}
            </button>
          </form>
          {formMessage.text && (
            <p className={`form-message ${formMessage.type}`}>{formMessage.text}</p>
          )}
        </div>

        {/* Leave Balance Card */}
        <div className="card">
          <h3>My Leave Balance</h3>
          {loading ? <p>Loading...</p> : (
            <div className="balance-grid">
              <div className="balance-item">
                <span>{balances?.casual_leave ?? 'N/A'}</span>
                <p>Casual Leave</p>
              </div>
              <div className="balance-item">
                <span>{balances?.sick_leave ?? 'N/A'}</span>
                <p>Sick Leave</p>
              </div>
              <div className="balance-item">
                <span>{balances?.earned_leave ?? 'N/A'}</span>
                <p>Earned Leave</p>
              </div>
            </div>
          )}
        </div>

        {/* Leave History Card */}
        <div className="card full-width-card">
          <h3>My Leave History</h3>
          {loading ? <p>Loading...</p> : (
            <div className="history-table-container">
              <table>
                <thead>
                  <tr>
                    <th>Request ID</th><th>Type</th><th>Start Date</th><th>Days</th><th>Reason</th><th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(history) && history.length > 0 ? history.map(req => (
                    <tr key={req.request_id}>
                      <td>{req.request_id}</td>
                      <td>{req.leave_type.replace('_', ' ')}</td>
                      <td>{req.start_date}</td>
                      <td>{req.number_of_days}</td>
                      <td>{req.reason}</td>
                      <td><span className={`status ${req.status}`}>{req.status}</span></td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan="6">No leave history found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};


// --- Main App Component (Unchanged) ---
function App() {
  const [user, setUser] = useState(null);

  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    localStorage.setItem('user', JSON.stringify(loggedInUser));
  };
  
  const handleLogout = () => {
      setUser(null);
      localStorage.removeItem('user');
  };

  useEffect(() => {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
          setUser(JSON.parse(savedUser));
      }
  }, []);

  return (
    <div className="App">
      {!user ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : (
        <Dashboard user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;
