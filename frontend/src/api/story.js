import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const generateStory = async (prompt, file = null) => {
  const formData = new FormData();
  formData.append("prompt", prompt);

  // Backend expects "file"
  if (file) {
    formData.append("file", file);
  }

  const res = await axios.post(`${BASE_URL}/upload`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.data;
};