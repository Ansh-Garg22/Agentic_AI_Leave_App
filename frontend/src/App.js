
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';
 
const API_URL = 'http://localhost:8080';


const invokeAgent = async (userId, userRole, query) => {
  try {
    const response = await axios.post(`${API_URL}/agent/invoke`, {
      user_id: userId,
      role: userRole, 
      query: query,
    });
    return response.data;
  } catch (error) {
    console.error(`Error invoking agent for query "${query}":`, error);
    throw error.response?.data?.detail || 'An agent error occurred. Please try again.';
  }
};


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
            onChange={(e) => { setUserId(e.target.value); setError(''); }}
            placeholder="e.g., user001"
          />
          <button type="submit">Login</button>
          {error && <p className="error-message">{error}</p>}
        </form>
        <p className="login-hint">Hint: Try `user001` (Manager) or `user002`, `user003` (Employees).</p>
      </div>
    </div>
  );
};

const EmployeeDashboard = ({ user, onLogout }) => {
    const [balances, setBalances] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [leaveType, setLeaveType] = useState('casual_leave');
    const [numberOfDays, setNumberOfDays] = useState(1);
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [reason, setReason] = useState('');
    const [formMessage, setFormMessage] = useState({ type: '', text: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchDashboardData = useCallback(async () => {
        setLoading(true);
        try {
            const [balanceResult, historyResult] = await Promise.all([
                invokeAgent(user.id, user.role, "Get my current leave balance."),
                invokeAgent(user.id, user.role, "Get my entire leave history.")
            ]);
            if (balanceResult?.balances) setBalances(balanceResult.balances);
            if (Array.isArray(historyResult?.requests)) setHistory(historyResult.requests);
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
            setFormMessage({ type: 'error', text: 'Could not load dashboard data. Please refresh.' });
        } finally {
            setLoading(false);
        }
    }, [user.id, user.role]);

    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    const handleApplyLeave = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setFormMessage({ type: '', text: '' });
        const query = `Apply for ${leaveType.replace('_', ' ')} for ${numberOfDays} days, starting on ${startDate}. The reason is: ${reason}`;
        try {
            const result = await invokeAgent(user.id, user.role, query);
            if (result.success) {
                setFormMessage({ type: 'success', text: result.message || 'Leave applied successfully!' });
                setLeaveType('casual_leave');
                setNumberOfDays(1);
                setReason('');
                await fetchDashboardData();
            } else {
                setFormMessage({ type: 'error', text: `Failed to apply: ${result.message || result.error}` });
            } 
        } catch (error) {
            setFormMessage({ type: 'error', text: `${error}` });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <h1>Welcome, {user.name} (Employee)</h1>
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
                            <input type="date" value={startDate} min={new Date().toISOString().split('T')[0]} onChange={e => setStartDate(e.target.value)} />
                        </div>
                        <div className="form-group full-width">
                            <label>Reason</label>
                            <textarea value={reason} onChange={e => setReason(e.target.value)} required />
                        </div>
                        <button type="submit" className="full-width" disabled={isSubmitting}>
                            {isSubmitting ? 'Submitting...' : 'Submit Request'}
                        </button>
                    </form>
                    {formMessage.text && <p className={`form-message ${formMessage.type}`}>{formMessage.text}</p>}
                </div>

                {/* Leave Balance Card */}
                <div className="card">
                    <h3>My Leave Balance</h3>
                    {loading ? <p>Loading...</p> : (
                        <div className="balance-grid">
                            <div className="balance-item"><span>{balances?.casual_leave ?? 'N/A'}</span><p>Casual</p></div>
                            <div className="balance-item"><span>{balances?.sick_leave ?? 'N/A'}</span><p>Sick</p></div>
                            <div className="balance-item"><span>{balances?.earned_leave ?? 'N/A'}</span><p>Earned</p></div>
                        </div>
                    )}
                </div>

                {/* Leave History Card */}
                <div className="card full-width-card">
                    <h3>My Leave History</h3>
                    <div className="history-table-container">
                        <table>
                            <thead><tr><th>ID</th><th>Type</th><th>Start</th><th>Days</th><th>Reason</th><th>Status</th></tr></thead>
                            <tbody>
                                {loading ? (<tr><td colSpan="6">Loading...</td></tr>) :
                                 Array.isArray(history) && history.length > 0 ? history.map(req => (
                                    <tr key={req.request_id}>
                                        <td>{req.request_id}</td><td>{req.leave_type.replace('_', ' ')}</td>
                                        <td>{req.start_date}</td><td>{req.number_of_days}</td>
                                        <td>{req.reason}</td><td><span className={`status ${req.status}`}>{req.status}</span></td>
                                    </tr>
                                )) : (<tr><td colSpan="6">No leave history found.</td></tr>)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
};


const ManagerDashboard = ({ user, onLogout }) => {
    const [pendingRequests, setPendingRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [isProcessing, setIsProcessing] = useState(null); // Track which request is being processed

    const fetchPendingRequests = useCallback(async () => {
        setLoading(true);
        setMessage({ type: '', text: '' });
        try {
            const result = await invokeAgent(user.id, user.role, "Show me all pending leave requests.");
            if (result.success && Array.isArray(result.requests)) {
                setPendingRequests(result.requests);
            } else {
                setPendingRequests([]);
                setMessage({ type: 'info', text: result.message || 'No pending requests found.' });
            }
        } catch (error) {
            console.error("Failed to fetch pending requests:", error);
            setMessage({ type: 'error', text: `${error}` });
        } finally {
            setLoading(false);
        }
    }, [user.id, user.role]);

    useEffect(() => {
        fetchPendingRequests();
    }, [fetchPendingRequests]);

    const handleManageRequest = async (requestId, action) => {
        setIsProcessing(requestId);
        setMessage({ type: '', text: '' });
        const query = `${action === 'approved' ? 'Approve' : 'Reject'} leave request ${requestId}`;
        try {
            const result = await invokeAgent(user.id, user.role, query);
            if (result.success) {
                setMessage({ type: 'success', text: result.message });
                // Refresh the list after a successful action
                await fetchPendingRequests();
            } else {
                setMessage({ type: 'error', text: `Action failed: ${result.error}` });
            }
        } catch (error) {
            setMessage({ type: 'error', text: `${error}` });
        } finally {
            setIsProcessing(null);
        }
    };

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <h1>Welcome, {user.name} (Manager)</h1>
                <button onClick={onLogout} className="logout-button">Logout</button>
            </header>
            <main className="dashboard-main">
                <div className="card full-width-card">
                    <h3>Pending Leave Requests</h3>
                    {message.text && <p className={`form-message ${message.type}`}>{message.text}</p>}
                    <div className="history-table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Request ID</th><th>User ID</th><th>Type</th>
                                    <th>Start Date</th><th>Days</th><th>Reason</th><th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (<tr><td colSpan="7">Loading requests...</td></tr>) :
                                pendingRequests.length > 0 ? pendingRequests.map(req => (
                                    <tr key={req.request_id}>
                                        <td>{req.request_id}</td>
                                        <td>{req.user_id}</td>
                                        <td>{req.leave_type.replace('_', ' ')}</td>
                                        <td>{req.start_date}</td>
                                        <td>{req.number_of_days}</td>
                                        <td>{req.reason}</td>
                                        <td>
                                            <div className="action-buttons">
                                                <button 
                                                  className="approve"
                                                  onClick={() => handleManageRequest(req.request_id, 'approved')}
                                                  disabled={isProcessing === req.request_id}>
                                                    {isProcessing === req.request_id ? '...' : 'Approve'}
                                                </button>
                                                <button 
                                                  className="reject"
                                                  onClick={() => handleManageRequest(req.request_id, 'rejected')}
                                                  disabled={isProcessing === req.request_id}>
                                                    {isProcessing === req.request_id ? '...' : 'Reject'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )) : (<tr><td colSpan="7">No pending requests to show.</td></tr>)}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
};


function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        setUser(JSON.parse(savedUser));
    }
  }, []);
  
  const handleLoginSuccess = (loggedInUser) => {
    setUser(loggedInUser);
    localStorage.setItem('user', JSON.stringify(loggedInUser));
  };
  
  const handleLogout = () => {
      setUser(null);
      localStorage.removeItem('user');
  };
//  react system
  return (
    <div className="App">
      {!user ? (
        <Login onLoginSuccess={handleLoginSuccess} />
      ) : user.role === 'manager' ? (
        <ManagerDashboard user={user} onLogout={handleLogout} />
      ) : (
        <EmployeeDashboard user={user} onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;