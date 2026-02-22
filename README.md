# OpenCompanyBot

AI-powered UK company registration API with MCP support.

## Features

- ⚡ Instant UK company registration via Companies House API
- 🤖 MCP-ready for AI agents
- 💳 USDT payments (ERC20/TRC20)
- 🌐 Deploys to Cloudflare Workers (global edge)

## Tech Stack

- **Backend**: Python FastAPI + Cloudflare Workers
- **Frontend**: Static HTML (EN/ZH)
- **CI/CD**: GitHub Actions
- **Payments**: CCPayment (USDT)
- **Company Data**: UK Companies House API

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/opencompanybot.git
cd opencompanybot
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `COMPANIES_HOUSE_API_KEY` - UK Companies House API key
- `CCPAYMENT_API_KEY` - CCPayment API key
- `CCPAYMENT_MERCHANT_ID` - CCPayment merchant ID
- `OPENROUTER_API_KEY` - OpenRouter API key (for AI features)

### 3. Run Locally

```bash
# Install Wrangler
npm install -g wrangler

# Run on local Cloudflare Workers
wrangler dev
```

### 4. Deploy

```bash
# Deploy API
wrangler deploy --env production

# Or use GitHub Actions (push to main branch)
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/companies/incorporate` | Register UK company |
| `GET /api/v1/companies/{company_number}` | Get company details |
| `POST /api/v1/payment/create` | Create USDT payment |
| `GET /api/v1/payment/status/{order_id}` | Check payment |
| `GET /api/v1/mcp/tools` | List MCP tools |
| `POST /api/v1/mcp/call` | Execute MCP tool |

## MCP Tools

- `register_uk_company` - Register a UK company
- `get_company_status` - Get company status
- `search_uk_companies` - Search companies
- `create_usdt_payment` - Create payment
- `verify_payment` - Verify payment

## Website

The website is in `web/public/` - static HTML with EN/ZH support.

### Build & Deploy

```bash
cd web
npm install
npm run build
# Deploy via Cloudflare Pages
```

## License

MIT
