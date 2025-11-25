# Fintela Risk Dashboard

A React-based dashboard for visualizing portfolio risk and fund performance metrics.

## Features

- **Real-time Data**: Auto-refreshes every 60 seconds
- **Risk Distribution**: Visual chart showing LOW/MEDIUM/HIGH risk portfolios
- **High-Risk Alerts**: Table of portfolios with HIGH risk scores
- **Poor Performers**: List of funds performing below peer average
- **Summary Cards**: Quick overview of key metrics

## Setup

1. Install dependencies:
```bash
cd dashboard
npm install
```

2. Make sure your FastAPI server is running on `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

4. Open your browser to `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## API Endpoints Used

- `GET /portfolios` - List all portfolios
- `GET /alerts/portfolios` - Get high-risk portfolios
- `GET /alerts/funds` - Get poor performing funds

