
import json
import os
from datetime import date
from pydantic import BaseModel, Field
import uuid
from typing import Literal

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.json')
LEAVE_REQUESTS_DB_PATH = os.path.join(DATA_DIR, 'leave_requests.json')

def read_json_db(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)

def write_json_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


class LeaveBalanceInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user, e.g., 'user001'.")

class ApplyLeaveInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user applying for leave.")
    leave_type: str = Field(description="The type of leave: 'casual_leave', 'sick_leave', or 'earned_leave'.")
    start_date: date = Field(description="The start date of the leave in YYYY-MM-DD format.")
    number_of_days: int = Field(description="The total number of days for the leave.")
    reason: str = Field(description="The reason for taking the leave.")

class CheckStatusInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user checking their leave status.")

class GetAllPendingRequestsInput(BaseModel):
    manager_id: str = Field(description="The user ID of the manager making the request, e.g., 'user001'.")

class ManageLeaveRequestInput(BaseModel):
    manager_id: str = Field(description="The user ID of the manager taking the action.")
    request_id: str = Field(description="The unique ID of the leave request to be managed, e.g., 'req_8949fb'.")
    action: Literal['approved', 'rejected'] = Field(description="The action to take: 'approved' or 'rejected'.")


def _is_manager(user_id: str, users: list) -> bool:
    
    for user in users:
        if user['user_id'] == user_id:
            return user.get('role') == 'manager'
    return False


def get_leave_balance(user_id: str) -> dict:
    
    users = read_json_db(USERS_DB_PATH)
    for user in users:
        if user['user_id'] == user_id:
            return {
                "success": True,
                "user_name": user['name'],
                "balances": user['leave_balances']
            }
    return {"success": False, "error": f"User with ID '{user_id}' not found."}


def apply_for_leave(user_id: str, leave_type: str, start_date: date, number_of_days: int, reason: str) -> dict:
    
    users = read_json_db(USERS_DB_PATH)
    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)

    if start_date < date.today():
        return {"success": False, "error": "Invalid start date. Cannot apply for leave in the past."}

    user_found = next((u for u in users if u['user_id'] == user_id), None)
    if not user_found:
        return {"success": False, "error": f"User with ID '{user_id}' not found."}
 
    if leave_type not in user_found['leave_balances']:
        return {"success": False, "error": f"Invalid leave type '{leave_type}'."}

    if user_found['leave_balances'][leave_type] < number_of_days:
        return {"success": False, "error": "Insufficient leave balance."}

    
    user_found['leave_balances'][leave_type] -= number_of_days
    write_json_db(USERS_DB_PATH, users)

    new_request = {
        "request_id": f"req_{uuid.uuid4().hex[:6]}",
        "user_id": user_id,
        "leave_type": leave_type,
        "start_date": start_date.isoformat(),
        "number_of_days": number_of_days,
        "reason": reason,
        "status": "pending"
    }
    leave_requests.append(new_request)
    write_json_db(LEAVE_REQUESTS_DB_PATH, leave_requests)

    return {
        "success": True,
        "message": "Leave application submitted and is now pending approval.",
        "request_id": new_request['request_id'],
        "new_balance": user_found['leave_balances'][leave_type]
    }


def check_leave_status(user_id: str) -> dict:
    
    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
    user_requests = [req for req in leave_requests if req['user_id'] == user_id]
    if not user_requests:
        return {"success": True, "requests": [], "message": f"No leave requests found for user '{user_id}'."}
    return {"success": True, "requests": user_requests}


def get_all_pending_requests(manager_id: str) -> dict:
    
    users = read_json_db(USERS_DB_PATH)
    if not _is_manager(manager_id, users):
        return {"success": False, "error": "Access denied. Only managers can view all pending requests."}

    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
    pending_requests = [req for req in leave_requests if req['status'] == 'pending']

    if not pending_requests:
        return {"success": True, "requests": [], "message": "No pending leave requests found."}

    return {"success": True, "requests": pending_requests}


def manage_leave_request(manager_id: str, request_id: str, action: str) -> dict:
    users = read_json_db(USERS_DB_PATH)

    if not _is_manager(manager_id, users):
        return {"success": False, "error": "Only managers can approve or reject leave requests."}

    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
    request_to_update = next((r for r in leave_requests if r['request_id'] == request_id), None)

    if not request_to_update:
        return {"success": False, "error": f"Leave request '{request_id}' not found."}
    
    if request_to_update['status'] != 'pending':
        return {"success": False, "error": f"Request '{request_id}' is already {request_to_update['status']}."}

    if action == 'approved':
        request_to_update['status'] = 'approved'

    elif action == 'rejected':
        request_to_update['status'] = 'rejected'
        employee_id = request_to_update['user_id']
        employee_user = next((u for u in users if u['user_id'] == employee_id), None)
 
        if employee_user:
            leave_type = request_to_update['leave_type']
            employee_user['leave_balances'][leave_type] += request_to_update['number_of_days']
            write_json_db(USERS_DB_PATH, users)
        else:
            request_to_update['status'] = 'pending'
            return {"success": False, "error": f"Employee '{employee_id}' not found. Action aborted."}

    write_json_db(LEAVE_REQUESTS_DB_PATH, leave_requests)
    return {"success": True, "message": f"Leave request '{request_id}' {action} successfully."}
