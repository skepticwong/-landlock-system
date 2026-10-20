import requests
res = requests.post('http://localhost:5000/api/auth/login', json={'phone': '000', 'password': '000'}, headers={'Origin': 'http://localhost:5173'})
print(res.status_code)
print(res.headers)
