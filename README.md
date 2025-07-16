## 🚀 Running the Project Locally

Follow the steps below to run both the backend and frontend of the project:

---

### 🔧 Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment (for PowerShell)
. .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create a `.env` file in the backend directory and add your API key and model name:
# Example:
# OPENROUTER_API_KEY=your_api_key_here
# OPENROUTER_MODEL=your_model_name_here

# Run the backend server
uvicorn api.main:app --reload --port 8080

cd frontend

# Install dependencies and start the development server
npm install
npm start
