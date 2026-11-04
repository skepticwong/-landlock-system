// src/lib/api.js
const API_BASE_URL = 'http://localhost:5000/api';
const BASE_URL = 'http://localhost:5000';

function clearStaleAuth() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

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

export async function fetchTransactions() {
  try {
    const token = localStorage.getItem('token');
    // Use the enriched /my endpoint from the multi-party approval routes
    const res = await fetch(`${API_BASE_URL}/transactions/my`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        clearStaleAuth();
      }
      const error = await res.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to load transactions');
    }
    
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

export async function fetchParcels() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/parcels`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.message || 'Failed to load parcels');
    }
    
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

// ── Marketplace / Listings ─────────────────────────────────

/** Fetch all active public listings (no auth needed) */
export async function fetchListings() {
  try {
    const res = await fetch(`${API_BASE_URL}/listings`);
    if (!res.ok) throw new Error('Failed to load listings');
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

/** Fetch only the current user's listings */
export async function fetchMyListings() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/listings/my`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      if (res.status === 401) {
        clearStaleAuth();
      }
      throw new Error('Failed to load your listings');
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

/** Fetch a single listing by id */
export async function fetchListing(id) {
  const res = await fetch(`${API_BASE_URL}/listings/${id}`);
  if (!res.ok) throw new Error('Listing not found');
  return res.json();
}

/** Create a new listing */
export async function createListing(data) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/listings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to create listing');
  return result;
}

/** Upload images for a listing */
export async function uploadListingImages(listingId, files) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  for (const file of files) {
    formData.append('images', file);
  }
  const res = await fetch(`${API_BASE_URL}/listings/${listingId}/images`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Image upload failed');
  return result;
}

/** Remove a listing (soft delete) */
export async function deleteListing(listingId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/listings/${listingId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to remove listing');
  return result;
}

/** Image base URL helper */
export function listingImageUrl(path) {
  return path ? `${BASE_URL}${path}` : null;
}

// ── Buyer Interests ─────────────────────────────────

/** Register interest in a listing */
export async function registerListingInterest(listingId, message = '') {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/listings/${listingId}/interest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message })
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to register interest');
  return result;
}

/** Fetch buyer interests for the current user's listings */
export async function fetchBuyerInterests() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/interests`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      if (res.status === 401) {
        clearStaleAuth();
      }
      throw new Error('Failed to load buyer interests');
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

/** Approve a buyer interest request */
export async function approveBuyerInterest(interestId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/interests/${interestId}/approve`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to approve interest');
  return result;
}

/** Reject a buyer interest request */
export async function rejectBuyerInterest(interestId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/interests/${interestId}/reject`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to reject interest');
  return result;
}

// ── Buyer's Own Interests ───────────────────────────────

/** Fetch buyer's own interests (what they've expressed interest in) */
export async function fetchMyInterests() {
  try {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/interests/my`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) {
      if (res.status === 401) {
        clearStaleAuth();
      }
      throw new Error('Failed to load your interests');
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

// ── Messages / Chat ─────────────────────────────────────

/** Fetch messages for a specific interest */
export async function fetchMessages(interestId) {
  try {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('No authentication token found');
    const res = await fetch(`${API_BASE_URL}/interests/${interestId}/messages`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to load messages');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

/** Send a message for a specific interest */
export async function sendMessage(interestId, message, messageType = 'text') {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE_URL}/interests/${interestId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message, message_type: messageType })
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.error || 'Failed to send message');
  return result;
}