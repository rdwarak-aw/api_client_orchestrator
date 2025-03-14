import sys
import time
import json
import requests
import schedule
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.logger import logger
from utils.token_manager import TokenManager
from utils.config_loader import config

class APIClient:
    """Client for making API requests with retries and exponential backoff."""
    
    def __init__(self, client_name, client_config, token_manager=None):
        self.client_name = client_name
        self.client_config = client_config
        self.api_url = client_config["url"]
        self.headers = client_config.get("headers", {})
        self.httpmethod = client_config.get("method", "GET")
        self.interval = client_config.get("interval", 15)
        self.token_manager = token_manager
        self.session = requests.Session()
        self.start_time = time.time()  # Track start time
        self.max_runtime = config.get("max_runtime", 0)
        #self.max_runtime = client_config.get("max_runtime", 0)  # Read from client config    

    def should_retry(exception):
        """Define retry conditions."""
        if isinstance(exception, requests.exceptions.RequestException):
            if hasattr(exception, 'response') and exception.response is not None:
                if 400 <= exception.response.status_code < 500:  # Client Errors (4xx)
                    return False  # Do not retry
            elif isinstance(exception, requests.exceptions.ConnectionError):
                return False  # Do not retry connection errors
        return True  # Retry other exceptions (e.g., timeouts, 5xx errors)

    """
    @retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception(should_retry),
    """

    @retry(
        stop=stop_after_attempt(3),  # Retry up to 3 times
        wait=wait_exponential(multiplier=1, min=2, max=30),  # Exponential backoff
        retry=retry_if_exception_type(requests.exceptions.RequestException),  # Retry only on network issues
    )    
    def call_api(self):
        """Make an API request with proper error handling."""
        try:
            if self.token_manager:
                self.headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
                logger.info(self.headers["Authorization"])

            # Read request type and payload from config
            method = self.client_config.get("method", "GET").upper()  # Default: GET
            payload = self.client_config.get("payload", {})  # Only used for POST
            
            # Send request based on method type
            if method == "POST":
                response = self.session.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            else:  # Default to GET
                response = self.session.get(self.api_url, headers=self.headers, timeout=10)
            
            if 400 <= response.status_code < 500:  # Client Errors
                logger.warning("[%s] Client error %s: %s", self.client_name, response.status_code, response.text)
                return  # No retries for 4xx errors

            if 500 <= response.status_code < 600:  # Server Errors
                logger.error("[%s] Server error %s: %s", self.client_name, response.status_code, response.text)
                raise requests.exceptions.HTTPError(f"Server error: {response.status_code}")

            # Process response
            try:
                data = response.json()  # Ensure response is JSON
                logger.info("[%s] Success: %s", self.client_name, data)
            except ValueError:
                logger.error("[%s] Invalid JSON response: %s", self.client_name, response.text)

        except requests.exceptions.Timeout:
            logger.error("[%s] API request timed out!", self.client_name)
        except requests.exceptions.ConnectionError:
            logger.error("[%s] Network error - could not connect to API!", self.client_name)
            logger.warning("[%s] will not be invoked again after max retries", self.client_name)
            return # No retries for Connection or Network errors
        except Exception as e:
            logger.exception("[%s] Unexpected error: %s", self.client_name, str(e))
        
    def run(self):
        """Schedule API calls at a fixed interval while handling shutdown gracefully."""
        schedule.every(self.interval).seconds.do(self.call_api)
        logger.info("[%s] Client started with interval %d seconds", self.client_name, self.interval)

        while True:
            try:
                elapsed_time = time.time() - self.start_time
                #logger.info("[%s] Total Elapsed time....", elapsed_time)
                if self.max_runtime > 0 and elapsed_time >= self.max_runtime:
                    logger.info("[%s] Max runtime reached! Shutting down...", self.client_name)
                    return  # Exit the loop and stop the client
            
                schedule.run_pending()
                time.sleep(1)
                """"
                # 🔹 Instead of fixed `time.sleep(1)`, sleep dynamically until the next task
                next_run = schedule.idle_seconds()  # Get time until next scheduled job
                if next_run is None:  # No more scheduled tasks
                    break
                time.sleep(max(0, next_run))  # Sleep exactly until the next scheduled task
                """
            except Exception as e:
                logger.exception("[%s] Error in run loop: %s", self.client_name, str(e))
                time.sleep(5)  # Avoid tight loop if an error occurs

def start_client(client_name, client_config, auth_config):
    """Starts an API client with optional token management, handling errors gracefully."""
    try:
        if not client_config:
            logger.error("Client configuration for '%s' is missing. Exiting...", client_name)
            sys.exit(1)

        use_token_manager = client_config.get("use_token_manager", False)
        logger.info("use_token_manager...%s", use_token_manager)
        token_manager = TokenManager(auth_config) if use_token_manager else None

        client = APIClient(client_name, client_config, token_manager)
        logger.info("[%s] Client initialized successfully.", client_name)
        
        client.run()
    
    except Exception as e:
        logger.exception("[%s] Unexpected error: %s", client_name, str(e))
        sys.exit(1)  # Exit only this client process

def main():
    """Main entry point for the client."""
    if len(sys.argv) < 3:
        logger.error("Usage: python client.py <client_name> <client_config_json> <auth_config_json>")
        sys.exit(1)

    client_name = sys.argv[1]
    
    try:
        client_config = json.loads(sys.argv[2])
        auth_config = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    except json.JSONDecodeError as e:
        logger.error("Failed to parse configuration JSON: %s", str(e))
        sys.exit(1)

    if not client_config:
        logger.error("Client configuration is missing for '%s'. Exiting...", client_name)
        sys.exit(1)
    
    start_client(client_name, client_config, auth_config)

if __name__ == "__main__":
    main()
