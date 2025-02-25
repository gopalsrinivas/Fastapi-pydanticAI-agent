"use client";

import { useState } from "react";

interface Message {
  role: "user" | "bot";
  text: string;
}

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/query/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      });

      const data = await res.json();
      setMessages([...newMessages, { role: "bot", text: data.response }]);
    } catch (error) {
      console.error("Error fetching response:", error);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-r from-blue-500 to-purple-600">
      <div className="w-full max-w-lg p-6 bg-white shadow-2xl rounded-xl">
        <h1 className="text-2xl font-bold text-center text-blue-600 mb-4">
          AI Chatbot
        </h1>

        <div className="chat-container bg-gray-50 p-4 h-80 rounded-lg shadow-inner overflow-y-auto">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`p-3 my-2 rounded-lg text-white ${
                msg.role === "user"
                  ? "bg-blue-500 text-right ml-auto"
                  : "bg-gray-500 text-left mr-auto"
              } w-fit max-w-xs`}
            >
              {msg.text}
            </div>
          ))}
        </div>

        <div className="flex flex-col mt-4">
          <textarea
            className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            className="mt-3 py-2 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 btn-modern"
            onClick={sendMessage}
          >
            🚀 Send
          </button>
        </div>
      </div>
    </div>
  );
}
