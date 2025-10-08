export type AgentStatus = "active" | "inactive" | "training" | "error";
export type AgentType =
  | "conversational"
  | "analytical"
  | "creative"
  | "automation";

export interface Agent {
  id: string;
  name: string;
  description: string;
  type: AgentType;
  status: AgentStatus;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  createdAt: string;
  lastActive: string;
  tasksCompleted: number;
  successRate: number;
  uptime: number;
  tags: string[];
  avatar?: string;
}

export interface AgentActivity {
  id: string;
  agentId: string;
  agentName: string;
  action: string;
  timestamp: string;
  status: "success" | "error" | "warning";
  details?: string;
}

export const agents: Agent[] = [
  {
    id: "1",
    name: "Customer Support Bot",
    description:
      "Handles customer inquiries and provides instant support across multiple channels",
    type: "conversational",
    status: "active",
    model: "GPT-4",
    temperature: 0.7,
    maxTokens: 2048,
    systemPrompt:
      "You are a helpful customer support assistant. Be friendly, professional, and solve customer issues efficiently.",
    createdAt: "2024-01-15",
    lastActive: "2 minutes ago",
    tasksCompleted: 1247,
    successRate: 94.5,
    uptime: 99.8,
    tags: ["support", "customer-service", "chat"],
    avatar: "https://github.com/personal-q.png",
  },
  {
    id: "2",
    name: "Data Analyst",
    description:
      "Analyzes complex datasets and generates insights with visualizations",
    type: "analytical",
    status: "active",
    model: "GPT-4",
    temperature: 0.3,
    maxTokens: 4096,
    systemPrompt:
      "You are a data analyst. Provide clear, accurate analysis with actionable insights.",
    createdAt: "2024-01-20",
    lastActive: "15 minutes ago",
    tasksCompleted: 856,
    successRate: 97.2,
    uptime: 98.5,
    tags: ["analytics", "data", "insights"],
    avatar: "https://github.com/yusufhilmi.png",
  },
  {
    id: "3",
    name: "Content Creator",
    description:
      "Generates creative content including blog posts, social media, and marketing copy",
    type: "creative",
    status: "active",
    model: "GPT-4",
    temperature: 0.9,
    maxTokens: 3072,
    systemPrompt:
      "You are a creative content writer. Generate engaging, original content that resonates with the target audience.",
    createdAt: "2024-02-01",
    lastActive: "1 hour ago",
    tasksCompleted: 543,
    successRate: 91.8,
    uptime: 97.3,
    tags: ["content", "marketing", "creative"],
    avatar: "https://github.com/kdrnp.png",
  },
  {
    id: "4",
    name: "Code Review Assistant",
    description:
      "Reviews code for best practices, bugs, and security vulnerabilities",
    type: "analytical",
    status: "training",
    model: "GPT-4",
    temperature: 0.2,
    maxTokens: 8192,
    systemPrompt:
      "You are a senior software engineer. Review code thoroughly for quality, security, and best practices.",
    createdAt: "2024-02-10",
    lastActive: "3 hours ago",
    tasksCompleted: 234,
    successRate: 88.5,
    uptime: 95.2,
    tags: ["code", "review", "development"],
    avatar: "https://github.com/yahyabedirhan.png",
  },
  {
    id: "5",
    name: "Email Automation",
    description: "Automates email responses and manages inbox workflows",
    type: "automation",
    status: "inactive",
    model: "GPT-3.5",
    temperature: 0.5,
    maxTokens: 1024,
    systemPrompt:
      "You are an email assistant. Draft professional, concise email responses.",
    createdAt: "2024-01-25",
    lastActive: "2 days ago",
    tasksCompleted: 1892,
    successRate: 96.1,
    uptime: 89.4,
    tags: ["email", "automation", "productivity"],
    avatar: "https://github.com/denizbuyuktas.png",
  },
  {
    id: "6",
    name: "Research Assistant",
    description:
      "Conducts research and summarizes findings from multiple sources",
    type: "analytical",
    status: "error",
    model: "GPT-4",
    temperature: 0.4,
    maxTokens: 4096,
    systemPrompt:
      "You are a research assistant. Gather information from reliable sources and provide comprehensive summaries.",
    createdAt: "2024-02-05",
    lastActive: "5 hours ago",
    tasksCompleted: 412,
    successRate: 92.7,
    uptime: 94.8,
    tags: ["research", "analysis", "summarization"],
    avatar: "https://github.com/shoaibux1.png",
  },
];

export const recentActivity: AgentActivity[] = [
  {
    id: "1",
    agentId: "1",
    agentName: "Customer Support Bot",
    action: "Completed 15 customer inquiries",
    timestamp: "2 minutes ago",
    status: "success",
  },
  {
    id: "2",
    agentId: "2",
    agentName: "Data Analyst",
    action: "Generated quarterly report",
    timestamp: "15 minutes ago",
    status: "success",
  },
  {
    id: "3",
    agentId: "6",
    agentName: "Research Assistant",
    action: "API rate limit exceeded",
    timestamp: "1 hour ago",
    status: "error",
    details: "Exceeded API quota. Please upgrade plan or wait for reset.",
  },
  {
    id: "4",
    agentId: "3",
    agentName: "Content Creator",
    action: "Created 5 blog post drafts",
    timestamp: "1 hour ago",
    status: "success",
  },
  {
    id: "5",
    agentId: "4",
    agentName: "Code Review Assistant",
    action: "Training on new dataset",
    timestamp: "3 hours ago",
    status: "warning",
    details: "Model training in progress. ETA: 2 hours",
  },
  {
    id: "6",
    agentId: "1",
    agentName: "Customer Support Bot",
    action: "Handled peak traffic successfully",
    timestamp: "4 hours ago",
    status: "success",
  },
];

export const agentStats = {
  totalAgents: agents.length,
  activeAgents: agents.filter((a) => a.status === "active").length,
  totalTasks: agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0),
  averageSuccessRate: (
    agents.reduce((sum, agent) => sum + agent.successRate, 0) / agents.length
  ).toFixed(1),
};
