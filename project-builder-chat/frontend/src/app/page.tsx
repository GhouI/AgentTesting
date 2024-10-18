"use client"
import { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Progress } from "@/components/ui/progress"

interface Message {
  role: string;
  content: string;
  downloadUrl?: string;
  isDownloading?: boolean;
  downloadProgress?: number;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [projectName, setProjectName] = useState('');
  const [backendUrl, setBackendUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://verbose-guacamole-qvv6jjw55xrcx5x4-5001.app.github.dev/';
    setBackendUrl(url);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !projectName.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${backendUrl}/api/build_project`, {
        project_description: input,
        project_name: projectName,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const newMessages: Message[] = response.data.messages.map((msg: any) => {
        if (msg.downloadUrl) {
          return { ...msg, isDownloading: false };
        }
        return msg;
      });

      setMessages((prev) => [...prev, ...newMessages]);
      
    } catch (error) {
      console.error('Error:', error);
      let errorMessage = 'An error occurred. Please try again.';
      if (axios.isAxiosError(error)) {
        if (error.response) {
          errorMessage = `Error: ${error.response.status} - ${error.response.data.error || error.message}`;
        } else if (error.request) {
          errorMessage = 'No response received from the server. Please check your connection.';
        } else {
          errorMessage = `Error: ${error.message}`;
        }
      }
      setMessages((prev) => [...prev, { role: 'system', content: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (downloadUrl: string, index: number) => {
    setMessages((prev) => 
      prev.map((msg, i) => i === index ? { ...msg, isDownloading: true, downloadProgress: 0 } : msg)
    );
    
    try {
      console.log(`Initiating download from URL: ${downloadUrl}`);
      const response = await axios.get(downloadUrl, {
        responseType: 'blob',
        onDownloadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total ?? 1));
          setMessages((prev) =>
            prev.map((msg, i) => i === index ? { ...msg, downloadProgress: percentCompleted } : msg)
          );
        }
      });
      console.log('Download response received:', response.status, response.headers);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'project.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      console.log('Download initiated in browser');
    } catch (error) {
      console.error('Download error:', error);
      if (axios.isAxiosError(error)) {
        console.error('Axios error details:', error.response?.data, error.response?.status, error.response?.headers);
      }
      setMessages((prev) => 
        prev.map((msg, i) => i === index ? { ...msg, content: msg.content + '\nError downloading file. Please try again.' } : msg)
      );
    } finally {
      setMessages((prev) => 
        prev.map((msg, i) => i === index ? { ...msg, isDownloading: false, downloadProgress: undefined } : msg)
      );
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">Project Builder Chat</h1>
        <ScrollArea className="h-[60vh] w-full border rounded-md p-4 mb-4">
          {messages.map((message, index) => (
            <div key={index} className={`mb-4 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
              <div className={`inline-block p-2 rounded-lg ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-black'}`}>
                <p className="font-bold">{message.role.charAt(0).toUpperCase() + message.role.slice(1)}</p>
                <p style={{whiteSpace: 'pre-wrap'}}>{message.content}</p>
                {message.downloadUrl && (
                  <div className="mt-2">
                    <Button 
                      onClick={() => handleDownload(message.downloadUrl!, index)}
                      disabled={message.isDownloading}
                      className="mb-2"
                    >
                      {message.isDownloading ? 'Downloading...' : 'Download Project'}
                    </Button>
                    {message.isDownloading && (
                      <Progress value={message.downloadProgress} className="w-full" />
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </ScrollArea>
        <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
          <Input
            placeholder="Project Name"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
          />
          <Textarea
            placeholder="Project Description"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Building Project...' : 'Send'}
          </Button>
        </form>
      </div>
    </main>
  );
}
