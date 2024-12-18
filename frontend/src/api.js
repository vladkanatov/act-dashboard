const API_URL = 'http://localhost:8000';

export const registerUser = async (username, password) => {
  const response = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return response.json();
};

export const loginUser = async (username, password) => {
  const response = await fetch(`${API_URL}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  });
  return response.json();
};

export const getAccounts = async (token) => {
  const response = await fetch(`${API_URL}/accounts`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
};

export const addAccount = async (token, accountName) => {
  const response = await fetch(`${API_URL}/accounts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ username: accountName }),
  });
  return response.json();
};

export const deleteAccount = async (token, accountId) => {
  const response = await fetch(`${API_URL}/accounts/${accountId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
};

export const sendMessage = async (token, ig_username, message) => {
  const response = await fetch(`${API_URL}/send_message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ig_username, message }),
  });
  return response.json();
};

export const analyzeFollowings = async (token, ig_username) => {
  const response = await fetch(`${API_URL}/analyze_followings/${ig_username}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.json();
};
