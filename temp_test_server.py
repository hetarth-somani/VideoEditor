import sys
try:
    from app import app
    print("App imported successfully.")
    with app.test_client() as client:
        response = client.get('/')
        print(f"Index route response status: {response.status_code}")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
