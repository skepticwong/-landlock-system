# backend/db/supabase.py
import requests
from config import config

class SupabaseClient:
    def __init__(self):
        self.base_url = f"{config.SUPABASE_URL}/rest/v1"
        self.headers = config.SUPABASE_HEADERS

    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            print(f"Supabase API error: {e}")
            raise

    def select(self, table, columns="*", eq=None, order=None):
        params = {"select": columns}
        if eq:
            for key, value in eq.items():
                params[f"{key}"] = f"eq.{value}"
        if order:
            params["order"] = order
        return self._make_request("GET", table, params=params)

    def insert(self, table, data):
        return self._make_request("POST", table, data=data)

    def update(self, table, data, eq=None):
        params = {}
        if eq:
            for key, value in eq.items():
                params[f"{key}"] = f"eq.{value}"
        return self._make_request("PATCH", table, data=data, params=params)

    def delete(self, table, eq):
        params = {}
        for key, value in eq.items():
            params[f"{key}"] = f"eq.{value}"
        return self._make_request("DELETE", table, params=params)

# Create a singleton instance
db = SupabaseClient()