import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const uploadStory = async (prompt, file) => {
  const formData = new FormData();
  formData.append('prompt', prompt);
  if (file) formData.append('file', file);

  const response = await axios.post(`${BASE_URL}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const chatWithPersona = async (prompt) => {
  const response = await axios.post(`${BASE_URL}/chat`, { message: prompt });
  return response.data;
};