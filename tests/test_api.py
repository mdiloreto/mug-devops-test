import os
import requests

ENDPOINT = os.getenv("TEST_ENDPOINT", "http://localhost:5000")
AZURE_ENDPOINT = os.getenv("TEST_AZURE_ENDPOINT")
AZURE_CREDENTIALS = os.getenv("TEST_AZURE_CREDENTIALS")
URL = os.getenv("TEST_URL", "https://madsblog.net/2024/10/29/kubernetes-networking-parte-2/")

def test_translate_missing_body():
    response = requests.post(f"{ENDPOINT}/api/translate", json=None)
    assert response.status_code == 500, f"Expected 500, but got {response.status_code}"

def test_translate_valid_translator():
    payload = {
        "url": URL,
        "translator_api": "azure",
        "azure_endpoint": AZURE_ENDPOINT,
        "azure_credentials": AZURE_CREDENTIALS,
    }
    response = requests.post(f"{ENDPOINT}/api/translate", json=payload, timeout=10)
    assert response.status_code == 200, f"Expected 200, but got {response.status_code}"
    
    # Poll the translation status
    translation_id = response.json().get("translation_id")  # Assuming API returns a job ID
    max_wait_time = 300  # Total wait time in seconds (5 minutes)
    interval = 10  # Poll every 10 seconds
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        status_response = requests.get(f"{ENDPOINT}/api/translate/status/{translation_id}")
        assert status_response.status_code == 200, f"Failed to get translation status: {status_response.text}"
        
        status = status_response.json().get("status")
        if status == "completed":
            # Verify the result
            output_response = requests.get(f"{ENDPOINT}/api/translate/result/{translation_id}")
            assert output_response.status_code == 200, f"Failed to get translation result: {output_response.text}"
            assert "output" in output_response.headers.get("Content-Disposition", ""), "Missing expected output file"
            break
        elif status == "failed":
            raise AssertionError(f"Translation failed: {status_response.json()}")
        
        time.sleep(interval)
        elapsed_time += interval
    else:
        raise TimeoutError("Translation did not complete within the expected time")

def test_translate_unsupported_translator():
    payload = {
        "url": URL,
        "translator_api": "unsupported",
    }
    response = requests.post(f"{ENDPOINT}/api/translate", json=payload, timeout=3600)
    assert response.status_code == 400, f"Expected 400, but got {response.status_code}"
    assert response.json()["error"] == "Translator 'unsupported' not supported by the API.", "Unexpected error message"
