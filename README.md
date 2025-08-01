# Ambivo GPT Actions Server

A FastAPI-based server that provides GPT Actions integration for Ambivo CRM, enabling ChatGPT to query and interact with CRM data using natural language.

## 🌟 Features

- **Natural Language Queries**: Ask questions about your CRM data in plain English
- **GPT Actions Integration**: Seamless ChatGPT plugin with OpenAPI 3.1.0 specification
- **Multiple Response Formats**: Table, natural language, or both
- **Secure Authentication**: JWT Bearer token authentication
- **Self-Contained**: No external MCP dependencies required
- **Railway Ready**: One-click deployment to Railway
- **Real-time Data**: Direct integration with Ambivo API endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Ambivo CRM account with API access
- Valid JWT authentication token

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ambivo-gpt
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
export AMBIVO_AUTH_TOKEN="your-jwt-token-here"
export AMBIVO_BASE_URL="https://goferapi.ambivo.com"  # Optional
```

4. **Run the server**
```bash
python main.py
```

The server will start on `http://localhost:8080`

### Using the CLI

```bash
# Start the server
python cli.py serve --host 0.0.0.0 --port 8080

# Generate OpenAPI schema
python cli.py generate-schema --output schema.yaml --format yaml
```

## 📡 API Endpoints

### Core Endpoints

- **`POST /query`** - Execute natural language queries
- **`GET /tools`** - List available tools
- **`POST /tools`** - Execute specific tools
- **`GET /health`** - Health check

### GPT Integration Endpoints

- **`GET /.well-known/ai-plugin.json`** - ChatGPT plugin manifest
- **`GET /openapi.json`** - OpenAPI 3.1.0 specification
- **`GET /`** - API documentation

## 🔍 Usage Examples

### Natural Language Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "show me leads created this week",
    "response_format": "both"
  }'
```

### List Available Tools

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8080/tools
```

### Direct Tool Execution

```bash
curl -X POST http://localhost:8080/tools \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "natural_query",
    "arguments": {
      "query": "count all contacts",
      "response_format": "natural"
    }
  }'
```

## 🚂 Railway Deployment

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_TEMPLATE_ID)

### Manual Deployment

1. **Connect to Railway**
```bash
railway login
railway init
```

2. **Set environment variables**
```bash
railway variables set AMBIVO_AUTH_TOKEN="your-jwt-token"
railway variables set AMBIVO_BASE_URL="https://goferapi.ambivo.com"
```

3. **Deploy**
```bash
railway up
```

Your server will be available at `https://your-app.railway.app`

## 🤖 ChatGPT Integration

### Create a GPT

1. **Go to ChatGPT** → Create a GPT
2. **Add Actions** → Import from URL
3. **Use your deployment URL**: `https://your-app.railway.app/openapi.json`
4. **Configure Authentication**:
   - Type: `Bearer`
   - Token: Your Ambivo JWT token

### GPT Configuration

```yaml
Name: Ambivo CRM Assistant
Description: Query and analyze your Ambivo CRM data using natural language
Instructions: |
  You are an AI assistant that helps users query their Ambivo CRM data.
  You can search for leads, contacts, opportunities, and other entities.
  Always use natural language to explain the results clearly.
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    ChatGPT      │───▶│  GPT Actions    │───▶│   Ambivo API    │
│                 │    │     Server      │    │                 │
│ Natural Language│    │                 │    │   CRM Data      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

- **`main.py`**: FastAPI server with all GPT endpoints
- **`mcp_core.py`**: Self-contained MCP functionality
- **`cli.py`**: Command-line interface
- **`schema_generator.py`**: OpenAPI schema generation
- **`config.py`**: Configuration management

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AMBIVO_AUTH_TOKEN` | JWT authentication token | Required |
| `AMBIVO_BASE_URL` | Ambivo API base URL | `https://goferapi.ambivo.com` |
| `AMBIVO_TIMEOUT` | Request timeout in seconds | `30.0` |
| `AMBIVO_MAX_RETRIES` | Maximum retry attempts | `3` |
| `PORT` | Server port (Railway sets this) | `8080` |

### Response Formats

- **`table`**: Structured data only
- **`natural`**: Natural language description only  
- **`both`**: Combined response (default)

## 🧪 Testing

### Run Local Tests

```bash
# Start the server
python main.py &

# Test health endpoint
curl http://localhost:8080/health

# Test with real token
curl -X POST http://localhost:8080/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "show me recent leads"}'
```

### Example Queries

- `"show me leads created this week"`
- `"how many contacts do we have?"`
- `"list opportunities worth more than $10,000"`
- `"find contacts with gmail addresses"`
- `"show me recent deals"`

## 📊 Monitoring

### Health Check

```bash
curl https://your-app.railway.app/health
```

### Debug Information

```bash
curl https://your-app.railway.app/debug
```

## 🔒 Security

- **JWT Authentication**: All API endpoints require valid Bearer tokens
- **Input Validation**: Query length and format validation
- **Rate Limiting**: Built-in request rate limiting
- **CORS**: Configured for ChatGPT domains
- **Error Handling**: Comprehensive error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/ambivo-gpt/issues)
- **Email**: dev@ambivo.com
- **Documentation**: [API Docs](https://your-app.railway.app/docs)

## 🛠️ Development

### Project Structure

```
ambivo-gpt/
├── main.py              # FastAPI server (entry point)
├── mcp_core.py          # Self-contained MCP functionality
├── cli.py               # Command-line interface
├── config.py            # Configuration management
├── schema_generator.py  # OpenAPI schema generation
├── requirements.txt     # Python dependencies
├── railway.json         # Railway deployment config
└── README.md           # This file
```

### Adding New Endpoints

1. Add the endpoint to `main.py`
2. Update the OpenAPI schema in `schema_generator.py`
3. Add corresponding tests
4. Update this README

## 🚨 Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Check token format
echo "YOUR_TOKEN" | base64 -d
```

**Connection Issues**
```bash
# Test API connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://goferapi.ambivo.com/entity/natural_query
```

**Deployment Issues**
```bash
# Check Railway logs
railway logs
```

## 📈 Roadmap

- [ ] GraphQL endpoint support
- [ ] WebSocket real-time updates
- [ ] Advanced query caching
- [ ] Multi-tenant support
- [ ] Enhanced monitoring and analytics
- [ ] Batch query processing

---

Made with ❤️ for the Ambivo community