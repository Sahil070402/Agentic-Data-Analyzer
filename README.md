# 🚀 Agentic Data Analyzer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **An intelligent, AI-powered data analysis platform that transforms natural language queries into comprehensive data insights, visualizations, and reports.**

## 🌟 Overview

The **Agentic Data Analyzer** is a cutting-edge data analysis application that leverages Microsoft's AutoGen framework and OpenAI's GPT models to provide intelligent, conversational data analysis. Simply upload your CSV data, ask questions in natural language, and receive automated insights complete with visualizations, statistical analysis, and actionable recommendations.

### 🎯 Key Highlights

- **🤖 Multi-Agent AI System**: Powered by specialized AI agents working collaboratively
- **💬 Multi-Chat Interface**: Manage multiple analysis sessions simultaneously
- **🧠 Query Intelligence**: Smart query analysis with contextual suggestions
- **🔒 Secure Execution**: All code runs in isolated Docker containers
- **📊 Rich Visualizations**: Automatic generation of charts, graphs, and plots
- **📁 Export Capabilities**: Download analysis results and visualizations
- **🎨 Intuitive UI**: Clean, modern Streamlit interface

## ✨ Features

### 🔥 Core Capabilities

| Feature | Description |
|---------|-------------|
| **Natural Language Queries** | Ask questions about your data in plain English |
| **Intelligent Query Suggestions** | Get contextual query recommendations based on your data |
| **Multi-Chat Sessions** | Work on multiple datasets simultaneously |
| **Real-time Analysis** | Stream analysis results as they're generated |
| **Secure Code Execution** | All Python code runs in isolated Docker containers |
| **Rich Visualizations** | Automatic generation of charts, plots, and graphs |
| **Export & Download** | Save analysis results, charts, and data files |
| **Session Management** | Persistent chat history and state management |

### 🤖 AI Agent Architecture

The application employs a sophisticated multi-agent system:

- **🔍 Query Clarity Agent**: Analyzes query clarity and provides suggestions
- **📊 Data Analyzer Agent**: Interprets requests and plans analysis approach
- **🐍 Python Code Executor**: Writes and executes Python code for analysis
- **🎯 Team Coordinator**: Orchestrates agent collaboration using RoundRobin methodology

### 🎨 Enhanced User Experience

- **Multi-Panel Interface**: Sidebar for chat management, main area for analysis
- **Smart Query Suggestions**: AI-generated clarifying questions for vague queries
- **Session-Specific File Management**: Track and export files per chat session
- **Real-time Feedback**: Live streaming of agent conversations and results
- **Clean File Management**: Automatic cleanup and organization of temporary files

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
├─────────────────────────────────────────────────────────────┤
│  Multi-Chat Interface │ Query Input │ File Upload │ Export  │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   AutoGen Team System                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Query Clarity   │ Data Analyzer   │ Python Code Executor    │
│ Agent           │ Agent           │ Agent                   │
│                 │                 │                         │
│ • Query Analysis│ • Task Planning │ • Code Generation       │
│ • Suggestions   │ • Data Insights │ • Secure Execution      │
│ • Context Aware │ • Coordination  │ • Result Processing     │
└─────────────────┴─────────────────┴─────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Docker Container                          │
├─────────────────────────────────────────────────────────────┤
│  Isolated Python Environment with Pre-installed Packages:  │
│  • pandas, numpy, matplotlib, seaborn                      │
│  • plotly, scipy, scikit-learn                            │
│  • openpyxl, xlsxwriter                                   │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
agentic-data-analyzer/
├── 📁 agents/                          # AI Agent Implementations
│   ├── 📄 code_executor_agent.py       # Python code execution agent
│   ├── 📄 data_analyzer_agent.py       # Data analysis planning agent
│   ├── 📄 query_clarity_agent.py       # Query intelligence agent
│   └── 📁 prompts/                     # Agent prompt templates
│       ├── 📄 __init__.py
│       └── 📄 data_analyzer_message.py
├── 📁 config/                          # Configuration & Utilities
│   ├── 📄 constants.py                 # Application constants
│   └── 📄 docker_utils.py              # Docker management utilities
├── 📁 models/                          # AI Model Clients
│   └── 📄 openai_model_client.py       # OpenAI API client
├── 📁 teams/                           # Agent Team Orchestration
│   └── 📄 analyzer_gpt.py              # Main agent team definition
├── 📁 temp/                            # Temporary file storage
│   └── 📄 .gitkeep                     # Preserve directory structure
├── 📄 main.py                          # CLI entry point
├── 📄 streamlit.py                     # Web application interface
├── 📄 Dockerfile                       # Custom Docker image
├── 📄 build_docker.bat                 # Windows Docker build script
├── 📄 build_docker.sh                  # Unix Docker build script
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .gitignore                       # Git ignore rules
├── 📄 ENHANCEMENT_SUMMARY.md           # Feature enhancement documentation
└── 📄 README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** 
- **Docker Desktop** (running)
- **OpenAI API Key**
- **Git** (for cloning)

### 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sahil070402/Agentic-Data-Analyzer.git
   cd Agentic-Data-Analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **⚡ Build optimized Docker image (Recommended)**
   
   This step pre-installs data science packages, reducing analysis startup time from 60s to <5s:
   
   ```bash
   # Windows
   build_docker.bat
   
   # macOS/Linux
   chmod +x build_docker.sh
   ./build_docker.sh
   ```

5. **Configure environment**
   
   Create `.env` file in project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

6. **Launch application**
   ```bash
   streamlit run streamlit.py
   ```

7. **Open in browser**
   
   Navigate to `http://localhost:8501`

## 💡 Usage Guide

### 🎯 Basic Workflow

1. **📤 Upload CSV**: Click "Upload your CSV file" and select your dataset
2. **❓ Ask Question**: Enter your analysis question in natural language
3. **🔍 Get Suggestions** (Optional): Click "Generate Query Suggestions" for ideas
4. **🚀 Analyze**: Click "Analyze Data" to start the AI analysis
5. **📊 View Results**: See real-time agent conversations and generated visualizations
6. **💾 Export**: Download analysis results and charts

### 🎨 Advanced Features

#### Multi-Chat Management
- **➕ New Chat**: Create separate analysis sessions
- **🔄 Switch Chats**: Toggle between different datasets/analyses
- **📋 Session Tracking**: Each chat maintains its own history and files

#### Query Intelligence
- **🤔 Vague Query Detection**: AI identifies unclear questions
- **💡 Smart Suggestions**: Get contextual query recommendations
- **🎯 Refined Analysis**: Use suggested queries for better results

#### Export & File Management
- **📥 Session Downloads**: Export all files from current chat
- **🗑️ Clean Workspace**: Remove temporary files to keep system clean
- **📊 Multiple Formats**: Charts (PNG), Data (CSV), Analysis (JSON)

### 📝 Example Queries

| Query Type | Example |
|------------|---------|
| **Descriptive** | "Show me summary statistics for all numerical columns" |
| **Visualization** | "Create a bar chart of sales by product category" |
| **Trend Analysis** | "Plot monthly revenue trends over time" |
| **Correlation** | "Show correlation between price and sales volume" |
| **Comparative** | "Compare performance across different regions" |
| **Statistical** | "Perform regression analysis on sales data" |

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes |
| `DOCKER_IMAGE` | Custom Docker image name | ❌ Optional |

### Docker Configuration

The application uses a custom Docker image with pre-installed packages:

- **Base**: Python 3.11 slim
- **Packages**: pandas, matplotlib, numpy, seaborn, plotly, scipy, scikit-learn
- **Benefits**: Faster analysis startup, consistent environment

## 🔧 Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug mode
streamlit run streamlit.py --server.runOnSave true

# Run CLI version
python main.py
```

### Adding New Agents

1. Create agent file in `agents/` directory
2. Implement agent class with required methods
3. Add agent to team in `teams/analyzer_gpt.py`
4. Update prompts in `agents/prompts/`

### Customizing Docker Environment

Modify `Dockerfile` to add new packages:

```dockerfile
RUN pip install --no-cache-dir \
    your-new-package==version
```

Then rebuild:
```bash
docker build -t agentic-analyzer-custom .
```

## 🚨 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Docker not starting** | Ensure Docker Desktop is running |
| **OpenAI API errors** | Check API key in `.env` file |
| **Package installation fails** | Use virtual environment |
| **Streamlit port conflict** | Use `--server.port 8502` |
| **Memory issues** | Increase Docker memory allocation |

### Debug Mode

Enable detailed logging:

```bash
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run streamlit.py
```

### Performance Optimization

- **Build Docker image**: Reduces startup time significantly
- **Use SSD storage**: Faster file I/O operations
- **Increase RAM**: Better performance for large datasets
- **Close unused chats**: Reduces memory usage

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/Agentic-Data-Analyzer.git

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run tests
python -m pytest tests/  # If tests are available
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Microsoft AutoGen**: Multi-agent conversation framework
- **OpenAI**: GPT models for intelligent analysis
- **Streamlit**: Beautiful web application framework
- **Docker**: Containerization and security
- **Python Data Science Stack**: pandas, matplotlib, numpy, seaborn

## 📞 Support

- **📧 Email**: [sahil070402@gmail.com](mailto:sahil070402@gmail.com)
- **🐛 Issues**: [GitHub Issues](https://github.com/Sahil070402/Agentic-Data-Analyzer/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/Sahil070402/Agentic-Data-Analyzer/discussions)

## 🔮 Roadmap

- [ ] **Multi-format Support**: Excel, JSON, Parquet files
- [ ] **Advanced Visualizations**: Interactive Plotly dashboards
- [ ] **ML Model Integration**: Automated model training and evaluation
- [ ] **Collaborative Features**: Share analysis sessions
- [ ] **API Endpoints**: REST API for programmatic access
- [ ] **Cloud Deployment**: One-click cloud deployment options

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by [Sahil Sareen](https://github.com/Sahil070402)

</div>
