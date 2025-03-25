import React, { useState } from 'react';
import { Send, RefreshCw } from 'lucide-react';
import type { Mistake } from '../types';

interface Props {
  darkMode: boolean;
}

export default function MistakeSection({ darkMode }: Props) {
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [formData, setFormData] = useState({
    teamLeader: '',
    agentName: '',
    ticketId: '',
    error: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newMistake: Mistake = {
      id: Date.now(),
      ...formData,
      timestamp: new Date().toLocaleTimeString()
    };
    setMistakes([newMistake, ...mistakes]);
    setFormData({ teamLeader: '', agentName: '', ticketId: '', error: '' });
  };

  return (
    <div className={`${darkMode ? 'text-white' : 'text-gray-900'}`}>
      <h2 className="text-3xl font-bold mb-8">Mistake Tracking</h2>

      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-6 mb-8">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Team Leader</label>
            <input
              type="text"
              value={formData.teamLeader}
              onChange={(e) => setFormData({ ...formData, teamLeader: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg ${
                darkMode
                  ? 'bg-gray-800 border-gray-700 text-white'
                  : 'bg-white border-gray-300 text-gray-900'
              } border focus:ring-2 focus:ring-blue-500`}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Agent Name</label>
            <input
              type="text"
              value={formData.agentName}
              onChange={(e) => setFormData({ ...formData, agentName: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg ${
                darkMode
                  ? 'bg-gray-800 border-gray-700 text-white'
                  : 'bg-white border-gray-300 text-gray-900'
              } border focus:ring-2 focus:ring-blue-500`}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Ticket ID</label>
            <input
              type="text"
              value={formData.ticketId}
              onChange={(e) => setFormData({ ...formData, ticketId: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg ${
                darkMode
                  ? 'bg-gray-800 border-gray-700 text-white'
                  : 'bg-white border-gray-300 text-gray-900'
              } border focus:ring-2 focus:ring-blue-500`}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Error Description</label>
          <textarea
            value={formData.error}
            onChange={(e) => setFormData({ ...formData, error: e.target.value })}
            className={`w-full h-[calc(100%-1.5rem)] px-4 py-2 rounded-lg ${
              darkMode
                ? 'bg-gray-800 border-gray-700 text-white'
                : 'bg-white border-gray-300 text-gray-900'
            } border focus:ring-2 focus:ring-blue-500`}
            required
          />
        </div>
      </form>

      <div className="flex space-x-4 mb-8">
        <button
          onClick={handleSubmit}
          className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Send size={20} />
          <span>Submit</span>
        </button>

        <button
          onClick={() => setMistakes([...mistakes])}
          className="flex items-center space-x-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <RefreshCw size={20} />
          <span>Refresh</span>
        </button>
      </div>

      <div className={`rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'} overflow-hidden shadow-xl`}>
        <table className="w-full">
          <thead className={darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium">Team Leader</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Agent</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Ticket ID</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Error</th>
              <th className="px-6 py-3 text-left text-sm font-medium">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {mistakes.map((mistake) => (
              <tr key={mistake.id}>
                <td className="px-6 py-4">{mistake.teamLeader}</td>
                <td className="px-6 py-4">{mistake.agentName}</td>
                <td className="px-6 py-4">{mistake.ticketId}</td>
                <td className="px-6 py-4">{mistake.error}</td>
                <td className="px-6 py-4">{mistake.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
