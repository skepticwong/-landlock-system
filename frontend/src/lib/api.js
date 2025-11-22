// src/lib/api.js
const API_BASE_URL = 'http://localhost:5000/api'; // Added /api prefix

export async function fetchPlots() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/plots`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to load plots');
    }
    
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

export async function registerPlot(plotData) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/plots`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(plotData)
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Save failed');
  return data;
}