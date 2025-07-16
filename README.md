RUN THE PROJECT BY USING THESE

#####################################################

cd backend 
#create a .env file and add your API key and MODEL NAME into it
python -m venv venv    
pip install -r requirements.txt    
. .\.venv\Scripts\Activate.ps1   

uvicorn api.main:app --reload --port 8080   

#####################################################

cd frontend
npm start
