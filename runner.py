import sys
import time
import subprocess
import signal
import json
from utils.logger import logger
from utils.config_loader import config

class Orchestrator:
    """Orchestrates multiple API clients, ensuring they run and shut down properly."""

    def __init__(self):
        self.processes = []

    def start_clients(self):
        """Starts API client processes using subprocess."""
        for client_name, client_config in config["clients"].items():
            auth_config = json.dumps(config.get("auth", {}))  # Convert auth config to JSON

            client_disabled = client_config.get("disabled", True)
            #logger.info("client_disabled ... %s", client_disabled)
            if(client_disabled):
                logger.info("Skipping the disabled Client...%s", client_name)
                continue

            client_config = json.dumps(client_config)  # Convert client config to JSON
            logger.info("client_config..%s", client_config)
            
            
            p = subprocess.Popen(["python", "client.py", client_name, client_config, auth_config])
            self.processes.append(p)
            logger.info(f"Started client: {client_name} (PID: {p.pid})")

    def shutdown(self, signum, frame):
        """Handles graceful shutdown of all client processes."""
        logger.info("Shutting down orchestrator and all clients...")

        for p in self.processes:
            logger.info(f"Terminating client {p.pid}...")
            p.terminate()  # Send SIGTERM to child process

        for p in self.processes:
            p.wait()  # Ensure cleanup before exiting

        logger.info("All clients terminated.")
        exit(0)

    def run(self):
        """Starts the orchestrator and monitors client processes for shutdown."""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
        logger.info("Starting all clients....")
        self.start_clients()

        # Monitor clients: Wait until all have exited
        while self.processes:
            for p in self.processes[:]:  # Iterate over a copy of the list
                retcode = p.poll()  # Check if process has exited
                if retcode is not None:  # Process finished
                    logger.info(f"Client process {p.pid} ({p.args[2]}) exited with code {retcode}")
                    self.processes.remove(p)  # Remove from active process list
        
            if not self.processes:  # If all clients are done, exit orchestrator
                logger.info("All clients have exited. Shutting down orchestrator...")
                sys.exit(0)  # Gracefully terminate orchestrator
        
        time.sleep(1)  # Avoid busy looping

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
