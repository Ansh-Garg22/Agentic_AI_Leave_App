# import json
# import os
# import uuid
# from datetime import date
# from typing import Literal

# from pydantic import BaseModel, Field
# from fastmcp import FastMCP

# DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
# USERS_DB_PATH = os.path.join(DATA_DIR, 'users.json')
# LEAVE_REQUESTS_DB_PATH = os.path.join(DATA_DIR, 'leave_requests.json')

# def read_json_db(path):
#     if not os.path.exists(path):
#         os.makedirs(os.path.dirname(path), exist_ok=True)
#         return []
#     with open(path, 'r') as f:
#         content = f.read()
#         if not content:
#             return []
#         return json.load(f)

# def write_json_db(path, data):
#     with open(path, 'w') as f:
#         json.dump(data, f, indent=2)

# # Create the FastMCP server
# mcp = FastMCP("LeaveManagementServer")

# # TOOL DEFINITIONS

# @mcp.tool()
# def get_leave_balance(user_id: str) -> dict:
#     """Fetch available leave balances (casual, sick, earned) for a user."""
#     users = read_json_db(USERS_DB_PATH)
#     for user in users:
#         if user['user_id'] == user_id:
#             return {
#                 "success": True,
#                 "user_name": user['name'],
#                 "balances": user['leave_balances']
#             }
#     return {"success": False, "error": f"User with ID '{user_id}' not found."}

# @mcp.tool()
# def apply_for_leave(user_id: str, leave_type: str, start_date: date, number_of_days: int, reason: str) -> dict:
#     """Apply for a leave by specifying user ID, leave type, days, start date, and reason."""
#     users = read_json_db(USERS_DB_PATH)
#     leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)

#     if start_date < date.today():
#         return {"success": False, "error": "Invalid start date. Cannot apply for leave in the past."}

#     user = next((u for u in users if u['user_id'] == user_id), None)
#     if not user:
#         return {"success": False, "error": f"User '{user_id}' not found."}
#     if leave_type not in user['leave_balances']:
#         return {"success": False, "error": f"Invalid leave type '{leave_type}'."}
#     if user['leave_balances'][leave_type] < number_of_days:
#         return {"success": False, "error": "Insufficient leave balance."}

#     user['leave_balances'][leave_type] -= number_of_days
#     write_json_db(USERS_DB_PATH, users)

#     new_request = {
#         "request_id": f"req_{uuid.uuid4().hex[:6]}",
#         "user_id": user_id,
#         "leave_type": leave_type,
#         "start_date": start_date.isoformat(),
#         "number_of_days": number_of_days,
#         "reason": reason,
#         "status": "pending"
#     }
#     leave_requests.append(new_request)
#     write_json_db(LEAVE_REQUESTS_DB_PATH, leave_requests)

#     return {"success": True, "message": "Leave request submitted.", "request_id": new_request["request_id"]}

# @mcp.tool()
# def check_leave_status(user_id: str) -> dict:
#     """Check the leave request history and status for a user."""
#     leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
#     user_requests = [req for req in leave_requests if req['user_id'] == user_id]
#     return {"success": True, "requests": user_requests}

# @mcp.tool()
# def get_all_pending_requests(manager_id: str) -> dict:
#     """Manager-only: View all pending leave requests."""
#     users = read_json_db(USERS_DB_PATH)
#     if not any(u['user_id'] == manager_id and u.get('role') == 'manager' for u in users):
#         return {"success": False, "error": "Only managers can view pending requests."}

#     leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
#     pending = [r for r in leave_requests if r['status'] == 'pending']
#     return {"success": True, "requests": pending}

# @mcp.tool()
# def manage_leave_request(manager_id: str, request_id: str, action: Literal['approved', 'rejected']) -> dict:
#     """Approve or reject a leave request (manager-only)."""
#     users = read_json_db(USERS_DB_PATH)
#     if not any(u['user_id'] == manager_id and u.get('role') == 'manager' for u in users):
#         return {"success": False, "error": "Only managers can manage requests."}

#     leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
#     req = next((r for r in leave_requests if r['request_id'] == request_id), None)
#     if not req:
#         return {"success": False, "error": f"Request '{request_id}' not found."}
#     if req['status'] != 'pending':
#         return {"success": False, "error": f"Request already {req['status']}."}

#     req['status'] = action
#     if action == 'rejected':
#         emp = next((u for u in users if u['user_id'] == req['user_id']), None)
#         if emp:
#             emp['leave_balances'][req['leave_type']] += req['number_of_days']
#             write_json_db(USERS_DB_PATH, users)

#     write_json_db(LEAVE_REQUESTS_DB_PATH, leave_requests)
#     return {"success": True, "message": f"Request '{request_id}' {action}."}

# if __name__ == "__main__":
#     from fastmcp import run
#     run(mcp)
