import requests

def test():
    # Register
    res = requests.post("http://localhost:8000/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "mypassword"
    })
    print("Register:", res.status_code, res.text)
    
    # Login
    res = requests.post("http://localhost:8000/login", data={
        "username": "testuser",
        "password": "mypassword"
    })
    print("Login:", res.status_code, res.text)

if __name__ == "__main__":
    test()
