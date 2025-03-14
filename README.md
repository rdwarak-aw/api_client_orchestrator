# API Client Orchestrator

## Overview
The API Client Orchestrator is responsible for managing multiple API clients, ensuring they start, run, and terminate properly. Each client runs as a separate subprocess and makes periodic API requests as per its configuration. The orchestrator also handles graceful shutdowns.

---

## Project Structure
'''
project-root/
�-- runner.py   # Manages and spawns API clients
�-- client.py         # Individual API client making requests
�-- utils/
�   +-- logger.py     # Logging utility
�   +-- config_loader.py # Loads configuration from config.json
�   +-- token_manager.py # Handles authentication tokens
�-- config.json       # Configuration file for clients and orchestrator
�-- README.md         # Documentation
'''

---

## Installation
### Prerequisites
- Python 3.12+
- Dependencies from 'requirements.txt'

### Steps
1. Clone the repository:
   '''sh
   git clone <repo_url>
   cd project-root
   '''
2. Install dependencies:
   '''sh
   pip install -r requirements.txt
   '''

---

## Configuration
The 'config.json' file holds configuration details for the orchestrator and clients. Example:

'''json
{
  "max_runtime": 3600,
  "use_token_manager": true,
  "auth": {
    "token_url": "https://auth.example.com/token",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  },
  "clients": {
    "client_A": {
      "url": "https://api.example.com/data",
      "interval": 30,
      "method": "GET"
    },
    "client_B": {
      "url": "https://api.example.com/upload",
      "interval": 60,
      "method": "POST"
    }
  }
}
'''

- **max_runtime**: Global timeout (in seconds) for all clients.
- **use_token_manager**: Whether authentication tokens should be managed.
- **auth**: Authentication details.
- **clients**: Defines API clients, their request intervals, and request methods.

---

## Running the Application
### Start the Orchestrator
'''sh
python runner.py
'''
This will:
- Load the configuration.
- Spawn API clients as subprocesses.
- Handle shutdown signals.

### Start an Individual Client (Standalone Testing)
'''sh
python client.py client_A '{"url": "https://api.example.com/data", "interval": 30, "method": "GET"}'
'''

---

## Logging
Logs are captured using 'logger.py' and include:
- Process IDs (PIDs)
- Client names
- API responses/errors

Example log entry:
'''
INFO - Client process 12345 (client_A) exited with code 0
WARNING - [client_B] API returned error 404: Not Found
'''

---

## Handling Shutdown
- **Graceful Termination:** Press 'CTRL + C' or send a 'SIGTERM' signal to 'runner.py'.
- Clients will terminate once 'max_runtime' is reached.

---

## Enhancements & Future Work
- Implement API retries with exponential backoff.
- Add support for dynamic client addition/removal.
- Improve error handling and resilience.

---

## Contributors
- GPT-4-turbo with Instructions from CMR+ Product Team