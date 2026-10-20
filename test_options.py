import requests
res = requests.options('http://localhost:5000/api/auth/login', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'Content-Type'})
print(res.status_code)
print(res.headers)
