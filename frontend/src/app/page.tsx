"use client";

import React, { useState, useEffect } from "react";
import { 
  MessageSquare, BarChart2, Shield, Upload, Search, 
  User, CheckCircle, AlertTriangle, Play, RefreshCw, Trash2, logOut 
} from "lucide-react";

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  
  // Navigation
  const [activeTab, setActiveTab] = useState<"copilot" | "analytics" | "knowledge" | "logs">("copilot");
  
  // Dashboard States
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | "">("");
  const [customerDetails, setCustomerDetails] = useState<any>(null);
  const [query, setQuery] = useState("");
  
  // AI Response state
  const [loadingAI, setLoadingAI] = useState(false);
  const [aiResponse, setAiResponse] = useState<any>(null);
  
  // RAG upload state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  
  // Analytics state
  const [analytics, setAnalytics] = useState<any>(null);
  
  // Logs state
  const [logs, setLogs] = useState<any[]>([]);
  
  // Base API URL
  const API_URL = "http://localhost:8000/api";

  // Login handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);
      
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) {
        throw new Error("Invalid username or password");
      }
      
      const data = await res.json();
      setToken(data.access_token);
      localStorage.setItem("copilot_token", data.access_token);
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem("copilot_token");
    setCustomerDetails(null);
    setAiResponse(null);
  };

  // Load configuration and data on token state
  useEffect(() => {
    const savedToken = localStorage.getItem("copilot_token");
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchCustomers();
    fetchAnalytics();
    fetchLogs();
  }, [token]);

  useEffect(() => {
    if (selectedCustomerId) {
      fetchCustomerDetails(selectedCustomerId as number);
    } else {
      setCustomerDetails(null);
    }
  }, [selectedCustomerId]);

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API_URL}/customers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCustomers(data);
        if (data.length > 0) setSelectedCustomerId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCustomerDetails = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/customers/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCustomerDetails(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`${API_URL}/analytics/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Query AI Copilot Agent
  const handleQueryAI = async () => {
    if (!selectedCustomerId || !query.trim()) return;
    setLoadingAI(true);
    setAiResponse(null);
    try {
      const formData = new FormData();
      formData.append("customer_id", String(selectedCustomerId));
      formData.append("query", query);
      
      const res = await fetch(`${API_URL}/copilot/query`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setAiResponse(data);
        // Refresh customer details to pull new memories
        fetchCustomerDetails(selectedCustomerId as number);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAI(false);
    }
  };

  // Clear memory handler
  const handleClearMemory = async () => {
    if (!selectedCustomerId) return;
    if (confirm("Are you sure you want to clear this customer's memories?")) {
      try {
        const res = await fetch(`${API_URL}/copilot/memories/${selectedCustomerId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          fetchCustomerDetails(selectedCustomerId as number);
        }
      } catch (err) {
        console.error(err);
      }
    }
  };

  // Handle PDF Ingestion
  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploadStatus("Uploading & processing PDF RAG pipeline...");
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      
      const res = await fetch(`${API_URL}/copilot/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        setUploadStatus(`Success! Ingested ${data.chunks_ingested} chunks from ${data.filename}.`);
        setUploadFile(null);
        fetchLogs();
      } else {
        const errData = await res.json();
        setUploadStatus(`Error: ${errData.detail || "Upload failed"}`);
      }
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message}`);
    }
  };

  // ----------------- LOGIN RENDER -----------------
  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600">
              <Shield className="h-6 w-6" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">AI Copilot Dashboard</h1>
            <p className="text-sm text-slate-400">Sign in to assist customer support agents</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-400">Email Address</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="agent@copilot.com"
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm text-white outline-none focus:border-violet-600 focus:ring-1 focus:ring-violet-600"
              />
            </div>
            
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-400">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm text-white outline-none focus:border-violet-600 focus:ring-1 focus:ring-violet-600"
              />
            </div>

            {authError && (
              <p className="text-xs text-rose-500">{authError}</p>
            )}

            <button 
              type="submit"
              className="mt-2 w-full rounded-lg bg-violet-600 py-3 font-semibold text-white transition-all hover:bg-violet-700 active:scale-[0.98]"
            >
              Sign In
            </button>
          </form>
          
          <div className="mt-6 text-center text-xs text-slate-500">
            Default credentials: <code className="text-slate-400">agent@copilot.com / agent123</code> or <code className="text-slate-400">admin@copilot.com / admin123</code>
          </div>
        </div>
      </div>
    );
  }

  // ----------------- MAIN DASHBOARD RENDER -----------------
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      
      {/* 1. Sidebar */}
      <aside className="w-64 border-r border-slate-900 bg-slate-900/30 p-6 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-3 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-sm leading-none">Copilot Portal</h2>
              <span className="text-xs text-violet-400">Enterprise AI</span>
            </div>
          </div>

          <nav className="space-y-1">
            <button 
              onClick={() => setActiveTab("copilot")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${activeTab === "copilot" ? "bg-violet-600 text-white font-medium" : "text-slate-400 hover:bg-slate-900"}`}
            >
              <MessageSquare className="h-4 w-4" />
              Copilot Workspace
            </button>
            
            <button 
              onClick={() => setActiveTab("analytics")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${activeTab === "analytics" ? "bg-violet-600 text-white font-medium" : "text-slate-400 hover:bg-slate-900"}`}
            >
              <BarChart2 className="h-4 w-4" />
              Analytics Dashboard
            </button>
            
            <button 
              onClick={() => setActiveTab("knowledge")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${activeTab === "knowledge" ? "bg-violet-600 text-white font-medium" : "text-slate-400 hover:bg-slate-900"}`}
            >
              <Upload className="h-4 w-4" />
              Upload Policies
            </button>
            
            <button 
              onClick={() => setActiveTab("logs")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${activeTab === "logs" ? "bg-violet-600 text-white font-medium" : "text-slate-400 hover:bg-slate-900"}`}
            >
              <Shield className="h-4 w-4" />
              Security Audit logs
            </button>
          </nav>
        </div>

        <button 
          onClick={handleLogout}
          className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-slate-400 text-xs hover:bg-red-950/20 hover:text-rose-500 transition-all"
        >
          Sign Out
        </button>
      </aside>

      {/* 2. Main Content Frame */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        
        {/* Header */}
        <header className="h-16 border-b border-slate-900 px-8 flex items-center justify-between bg-slate-900/10">
          <h1 className="text-lg font-semibold capitalize">
            {activeTab === "copilot" ? "AI Customer Support Copilot" : `${activeTab} Dashboard`}
          </h1>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span className="flex items-center gap-1.5"><User className="h-4 w-4 text-violet-400" /> Active Support Session</span>
          </div>
        </header>

        {/* Dynamic Tab Body */}
        <div className="flex-1 p-8">
          
          {/* TAB 1: COPILOT WORKSPACE */}
          {activeTab === "copilot" && (
            <div className="grid grid-cols-12 gap-8 h-full min-h-[500px]">
              
              {/* Left Column: Customer context & timeline */}
              <div className="col-span-4 flex flex-col gap-6">
                
                {/* Search Customer */}
                <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-5">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Select Customer Profile</h3>
                  <div className="relative">
                    <select
                      value={selectedCustomerId}
                      onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm outline-none focus:border-violet-600 focus:ring-1 focus:ring-violet-600 appearance-none"
                    >
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>{c.name} ({c.subscription_plan})</option>
                      ))}
                    </select>
                  </div>
                  
                  {customerDetails && (
                    <div className="mt-4 pt-4 border-t border-slate-900 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Email:</span>
                        <span className="font-medium text-slate-200">{customerDetails.customer.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Phone:</span>
                        <span className="font-medium text-slate-200">{customerDetails.customer.phone}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Plan:</span>
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-violet-950 text-violet-400">{customerDetails.customer.subscription_plan}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Billing:</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${customerDetails.customer.billing_status === "Paid" ? "bg-emerald-950 text-emerald-400" : "bg-rose-950 text-rose-400"}`}>
                          {customerDetails.customer.billing_status}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Persistent Memories */}
                {customerDetails && (
                  <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">AI persistent memory (Mem0)</h3>
                        <button 
                          onClick={handleClearMemory}
                          className="text-slate-500 hover:text-rose-500 transition-colors"
                          title="Clear memories"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      {customerDetails.memories.length === 0 ? (
                        <p className="text-xs text-slate-500 italic">No memories stored yet. Memory is extracted dynamically during chat sessions.</p>
                      ) : (
                        <ul className="space-y-2 overflow-y-auto max-h-[160px] pr-2">
                          {customerDetails.memories.map((m: string, i: number) => (
                            <li key={i} className="text-xs bg-slate-950 border border-slate-900/40 p-2.5 rounded-lg text-slate-300">
                              {m}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Orders Timeline */}
                {customerDetails && (
                  <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-5 max-h-[220px] overflow-y-auto">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Recent Orders</h3>
                    {customerDetails.orders.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No orders found.</p>
                    ) : (
                      <div className="space-y-2">
                        {customerDetails.orders.map((o: any) => (
                          <div key={o.id} className="text-xs border-l-2 border-violet-600 bg-slate-950 p-2 rounded-r-lg flex justify-between">
                            <div>
                              <p className="font-semibold text-slate-300">{o.product_name}</p>
                              <p className="text-[10px] text-slate-500">{new Date(o.created_at).toLocaleDateString()}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-violet-400">${o.price}</p>
                              <span className="text-[10px] text-slate-400 capitalize">{o.status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Center Panel: Copilot execution query */}
              <div className="col-span-5 flex flex-col gap-6">
                <div className="flex-1 rounded-xl border border-slate-900 bg-slate-900/20 p-6 flex flex-col justify-between">
                  <div className="flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="h-5 w-5 text-violet-500" />
                        <h2 className="text-sm font-semibold">Generate Suggested Reply</h2>
                      </div>
                      
                      <div className="mb-4">
                        <label className="text-xs text-slate-400 mb-1.5 block">Describe customer query or issue:</label>
                        <textarea
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="e.g. Alice Johnson is asking about why she was charged twice on her card."
                          className="w-full h-32 rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm outline-none resize-none focus:border-violet-600 focus:ring-1 focus:ring-violet-600"
                        />
                      </div>
                    </div>

                    <button
                      onClick={handleQueryAI}
                      disabled={loadingAI || !query.trim()}
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-violet-600 text-white font-semibold hover:bg-violet-700 active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none transition-all"
                    >
                      {loadingAI ? (
                        <>
                          <RefreshCw className="h-4 w-4 animate-spin" /> Querying LangGraph Agents...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" /> Run AI Copilot Flow
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* AI Response Display */}
                {aiResponse && (
                  <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-900 pb-3">
                      <div>
                        <span className="text-xs text-slate-400">Agent Proposed Reply:</span>
                        <div className="flex gap-2 mt-1">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-semibold">{aiResponse.category}</span>
                          <span className="flex items-center gap-1 text-[10px] text-slate-400">
                            Confidence: 
                            <strong className={aiResponse.confidence_score >= 0.8 ? "text-emerald-400" : "text-amber-500"}>
                              {Math.round(aiResponse.confidence_score * 100)}%
                            </strong>
                          </span>
                        </div>
                      </div>
                      
                      {aiResponse.escalate ? (
                        <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-amber-950 text-amber-500 border border-amber-900 rounded-lg">
                          <AlertTriangle className="h-3 w-3" /> Escalation Recommended
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-emerald-950 text-emerald-500 border border-emerald-900 rounded-lg">
                          <CheckCircle className="h-3 w-3" /> Auto-resolvable
                        </span>
                      )}
                    </div>

                    <div className="p-4 rounded-lg bg-slate-950 border border-slate-900/60 max-h-[160px] overflow-y-auto">
                      <p className="text-xs leading-relaxed text-slate-300 whitespace-pre-line">{aiResponse.suggested_reply}</p>
                    </div>

                    <div className="flex gap-3 text-xs justify-end">
                      <button 
                        onClick={() => {
                          navigator.clipboard.writeText(aiResponse.suggested_reply);
                          alert("Reply copied to clipboard!");
                        }}
                        className="px-4 py-2 border border-slate-800 bg-slate-900/40 rounded-lg hover:bg-slate-900 text-slate-300 font-semibold transition-all"
                      >
                        Copy to Clipboard
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Right Panel: Retrieved knowledge snippets */}
              <div className="col-span-3 rounded-xl border border-slate-900 bg-slate-900/20 p-5 overflow-y-auto max-h-[550px]">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Retrieved Knowledge Base (RAG)</h3>
                
                {aiResponse && aiResponse.retrieved_kb && aiResponse.retrieved_kb.length > 0 ? (
                  <div className="space-y-4">
                    {aiResponse.retrieved_kb.map((snippet: string, idx: number) => (
                      <div key={idx} className="p-3.5 rounded-lg bg-slate-950 border border-slate-900/50 space-y-2 text-xs">
                        <div className="flex justify-between items-center text-[10px] text-slate-500">
                          <span>Snippet #{idx + 1}</span>
                          <span className="text-violet-400 font-mono">Similarity Match</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed font-sans">{snippet}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-500 italic">No snippets retrieved yet. Run a query to index semantic matches.</p>
                    
                    <div className="p-3 rounded-lg border border-slate-900 bg-slate-950 text-[11px] text-slate-500">
                      <strong>Seeded Policy Docs:</strong>
                      <ul className="list-disc pl-4 mt-2 space-y-1">
                        <li>Refund Policy (30 days limit)</li>
                        <li>SLA Guidelines (Enterprise 1hr response)</li>
                        <li>Cloud Hosting Activation Manual</li>
                        <li>API Access limits</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: ANALYTICS DASHBOARD */}
          {activeTab === "analytics" && (
            <div className="space-y-8">
              {analytics ? (
                <>
                  {/* Grid summary cards */}
                  <div className="grid grid-cols-4 gap-6">
                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6 text-center">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Average Handling Time</p>
                      <h2 className="text-3xl font-extrabold text-violet-400">{analytics.avg_handling_time_sec}s</h2>
                    </div>

                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6 text-center">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">CSAT Score</p>
                      <h2 className="text-3xl font-extrabold text-emerald-400">{analytics.csat_score} / 5.0</h2>
                    </div>

                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6 text-center">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Resolution Rate</p>
                      <h2 className="text-3xl font-extrabold text-blue-400">{analytics.resolution_rate}%</h2>
                    </div>

                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6 text-center">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Top Complaint Category</p>
                      <h2 className="text-lg font-bold text-slate-200 capitalize mt-2">
                        {Object.keys(analytics.top_categories).length > 0 ? Object.keys(analytics.top_categories)[0] : "None"}
                      </h2>
                    </div>
                  </div>

                  {/* Visual breakdowns */}
                  <div className="grid grid-cols-2 gap-8">
                    {/* Sentiment trends */}
                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6">
                      <h3 className="text-sm font-semibold mb-4 text-slate-300">Sentiment Distribution</h3>
                      <div className="space-y-4">
                        {Object.entries(analytics.sentiment_trends).map(([sentiment, count]: any) => (
                          <div key={sentiment}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="capitalize">{sentiment}</span>
                              <span className="font-semibold text-slate-300">{count} occurrences</span>
                            </div>
                            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${sentiment === "Positive" ? "bg-emerald-500" : sentiment === "Negative" ? "bg-rose-500" : "bg-slate-500"}`}
                                style={{ width: `${count > 0 ? (count / Object.values(analytics.sentiment_trends).reduce((a:any, b:any)=>a+b, 0) as number) * 100 : 0}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Complaint Category breakdown */}
                    <div className="rounded-xl border border-slate-900 bg-slate-900/20 p-6">
                      <h3 className="text-sm font-semibold mb-4 text-slate-300">Category Distribution</h3>
                      <div className="space-y-4">
                        {Object.entries(analytics.top_categories).map(([category, count]: any) => (
                          <div key={category}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="capitalize">{category}</span>
                              <span className="font-semibold text-slate-300">{count} tickets</span>
                            </div>
                            <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-violet-600"
                                style={{ width: `${count > 0 ? (count / Object.values(analytics.top_categories).reduce((a:any, b:any)=>a+b, 0) as number) * 100 : 0}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin mx-auto text-violet-500 mb-3" />
                  <p className="text-sm text-slate-400">Loading analytics metrics...</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: KNOWLEDGE BASE PDF INGESTION */}
          {activeTab === "knowledge" && (
            <div className="max-w-2xl mx-auto rounded-xl border border-slate-900 bg-slate-900/20 p-8 space-y-6">
              <div className="text-center">
                <Upload className="h-10 w-10 text-violet-500 mx-auto mb-3" />
                <h2 className="text-lg font-semibold">Upload Company PDF Documents</h2>
                <p className="text-xs text-slate-400 mt-1">Chunk documents and populate ChromaDB vector indices for semantic search.</p>
              </div>

              <form onSubmit={handleFileUpload} className="space-y-4 pt-4 border-t border-slate-900">
                <div className="border-2 border-dashed border-slate-800 rounded-lg p-8 text-center bg-slate-950/40 hover:bg-slate-950/80 transition-all relative">
                  <input 
                    type="file" 
                    accept=".pdf"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setUploadFile(e.target.files[0]);
                      }
                    }}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  {uploadFile ? (
                    <p className="text-sm text-violet-400 font-semibold">{uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)</p>
                  ) : (
                    <p className="text-xs text-slate-500">Drag & drop your PDF file here, or click to browse</p>
                  )}
                </div>

                <button 
                  type="submit"
                  disabled={!uploadFile}
                  className="w-full py-3 rounded-lg bg-violet-600 text-white font-semibold hover:bg-violet-700 active:scale-[0.98] disabled:opacity-45 disabled:pointer-events-none transition-all"
                >
                  Upload & Ingest into ChromaDB
                </button>
              </form>

              {uploadStatus && (
                <div className="p-3 bg-slate-950 border border-slate-900 rounded-lg text-xs text-slate-400 text-center font-mono">
                  {uploadStatus}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SYSTEM AUDIT LOGS */}
          {activeTab === "logs" && (
            <div className="rounded-xl border border-slate-900 bg-slate-900/20 overflow-hidden">
              <div className="h-[450px] overflow-y-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-900 bg-slate-900/40 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="p-4">Timestamp</th>
                      <th className="p-4">Action</th>
                      <th className="p-4">Details</th>
                    </tr>
                  </thead>
                  <tbody className="text-xs divide-y divide-slate-900/40">
                    {logs.map((log: any) => (
                      <tr key={log.id} className="hover:bg-slate-900/10">
                        <td className="p-4 text-slate-500 whitespace-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                        <td className="p-4 font-semibold text-violet-400">{log.action}</td>
                        <td className="p-4 text-slate-300">{log.details}</td>
                      </tr>
                    ))}
                    {logs.length === 0 && (
                      <tr>
                        <td colSpan={3} className="p-8 text-center text-slate-500 italic">No system audit logs found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
