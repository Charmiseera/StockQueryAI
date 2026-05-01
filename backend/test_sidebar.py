import requests
import json

def test():
    token = requests.post('http://localhost:8000/login', data={'username': 'bob', 'password': 'pass'}).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    queries = [
        'Can you show me all our fruits and vegetables?',
        'Show me all the dairy products we have.',
        'What grains and pulses do we have in stock?',
        'Can you list all the seafood products?',
        'Show me all of our beverages.'
    ]

    for q in queries:
        try:
            print(f"Q: {q}")
            res = requests.post('http://localhost:8000/query', json={'question': q}, headers=headers).json()
            print(f"Tool: {res.get('tool_used')}")
            data = res.get('data')
            print(f"Data rows: {len(data) if isinstance(data, list) else (1 if data else 0)}")
            print(f"Answer: {res.get('answer')[:100]}...")
            print("-" * 40)
        except Exception as e:
            print(f"Failed {q}: {e}")

if __name__ == "__main__":
    test()
