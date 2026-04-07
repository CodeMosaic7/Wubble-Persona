import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const MOCK = import.meta.env.VITE_MOCK_API === "true";

const MOCK_RESPONSE = {
  streaming: {
    final_audio_url:
      "https://wubble-api-outputs-prod.s3.ap-southeast-1.amazonaws.com/gen5-audio/38181783-11d7-4855-94f9-d50205e0f61c/0/audio.mp3",
  },
  results: {
    custom_data: {
      audios: [
        {
          duration_seconds: 108.47,
          lyrics_sections: [
            {
              section_type: "verse",
              start: 400,
              end: 13040,
              lines: [
                { text: "The calendar page finally turns", start: 400, end: 3400 },
                { text: "A brand new chapter now has begun", start: 3640, end: 6320 },
              ],
            },
            {
              section_type: "chorus",
              start: 31080,
              end: 43720,
              lines: [
                { text: "Oh, the world is yours tonight", start: 31080, end: 33680 },
                { text: "Shining ever so bright", start: 34520, end: 37880 },
              ],
            },
          ],
        },
      ],
    },
  },
};

export const generateStory = async (prompt, file = null) => {
  if (MOCK) {
    await new Promise((r) => setTimeout(r, 2000)); // simulate latency
    return parseResponse(MOCK_RESPONSE);
  }

  const formData = new FormData();
  formData.append("prompt", prompt);
  if (file) formData.append("file", file);

  const res = await axios.post(`${BASE_URL}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return parseResponse(res.data);
};

function parseResponse(data) {
  const audio = data?.results?.custom_data?.audios?.[0];
  return {
    audioUrl: data?.streaming?.final_audio_url || null,
    duration: audio?.duration_seconds || null,
    lyricsSections: audio?.lyrics_sections || [],
  };
}