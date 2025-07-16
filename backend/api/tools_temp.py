import json
import os
from datetime import date
from pydantic import BaseModel, Field
import uuid

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.json')
LEAVE_REQUESTS_DB_PATH = os.path.join(DATA_DIR, 'leave_requests.json')

def read_json_db(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        data = json.load(f)
        if 'users.json' in path:
            print("Users loaded from:", USERS_DB_PATH)
        return data

def write_json_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

class LeaveBalanceInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user, e.g., 'user001'.")

class ApplyLeaveInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user applying for leave.")
    leave_type: str = Field(description="The type of leave being applied for (e.g., 'casual_leave', 'sick_leave').")
    start_date: date = Field(description="The start date of the leave in YYYY-MM-DD format.")
    number_of_days: int = Field(description="The total number of days for the leave.")
    reason: str = Field(description="The reason for taking the leave.")

class CheckStatusInput(BaseModel):
    user_id: str = Field(description="The unique identifier of the user checking their leave status.")


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


import uuid
from datetime import date 

def apply_for_leave(user_id: str, leave_type: str, start_date: date, number_of_days: int, reason: str) -> dict:
    
    users = read_json_db(USERS_DB_PATH)
    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)

    today = date.today()
    if start_date < today:
        return {
            "success": False,
            "error": "Invalid start date.",
            "message": "Leave application cannot be submitted for a past date."
        }

    user_found = None
    user_index = -1
    for i, u in enumerate(users):
        if u['user_id'] == user_id:
            user_found = u
            user_index = i
            break

    if not user_found:
        return {"success": False, "error": f"User with ID '{user_id}' not found."}

    if leave_type not in user_found['leave_balances']:
        return {"success": False, "error": f"Invalid leave type '{leave_type}'. Available types are: {list(user_found['leave_balances'].keys())}"}

    available_balance = user_found['leave_balances'][leave_type]

    if available_balance < number_of_days:
        return {
            "success": False,
            "error": "Insufficient leave balance.",
            "message": f"Requested {number_of_days} days of {leave_type}, but only {available_balance} are available."
        }

    users[user_index]['leave_balances'][leave_type] -= number_of_days
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
        "message": "Leave application successful and pending.",
        "request_id": new_request['request_id'],
        "new_balance": users[user_index]['leave_balances'][leave_type]
    }


def check_leave_status(user_id: str) -> dict:
    
    leave_requests = read_json_db(LEAVE_REQUESTS_DB_PATH)
    user_requests = [req for req in leave_requests if req['user_id'] == user_id]
    
    if not user_requests:
        return {"success": True, "requests": [], "message": f"No leave requests found for user '{user_id}'."}
        
    return {"success": True, "requests": user_requests}


