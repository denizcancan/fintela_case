# Fintela Case Study

A system for processing Turkish fund data, managing investment portfolios, and computing analytical metrics (risk & performance) using data pipelines.

> 📖 **For detailed architecture and design decisions, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

---

# **Quick Start**

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (if running locally without Docker)
- `uv` package manager ([install here](https://docs.astral.sh/uv/))

## Setup (One Command)

```bash
# Clone the repository
git clone <repository-url>
cd fintela-swe-case

# Make setup script executable (if needed)
chmod +x scripts/setup.sh

# Run setup script (starts Docker, loads data)
./scripts/setup.sh
```

**Note**: If you get a "Permission denied" error, you can also run:
```bash
bash scripts/setup.sh
```

That's it! All services will be running:
- **FastAPI**: http://localhost:8000
- **Dagster**: http://localhost:3000  
- **Dashboard**: http://localhost:5173

## Manual Setup

If you prefer to set up manually:


1. **Start Docker services**:
   ```bash
   docker-compose up -d
   ```

2. **Load fund_labels CSV**:
   ```bash
   uv run python scripts/init_db.py
   ```

3. **Create test portfolios** (optional):
   ```bash
   uv run python create_test_portfolios.py
   ```

---



## Database Tables

All tables are **automatically created** when PostgreSQL starts via Docker Compose:
- `portfolios` - Portfolio definitions
- `portfolio_positions` - Fund positions in portfolios
- `fund_labels` - Fund metadata (loaded from CSV)
- `fund_prices` - Daily fund prices (created by Dagster)
- `instrument_distributions` - Fund instrument distributions (created by Dagster)
- `portfolio_risk_scores` - Portfolio risk calculations
- `fund_performance_metrics` - Fund performance metrics

## Running Locally (Without Docker)

If you have PostgreSQL installed locally:

1. Create database:
   ```bash
   createdb fintela
   ```

2. Run SQL scripts:
   ```bash
   psql -d fintela -f portfolios.sql
   psql -d fintela -f risk_scores.sql
   psql -d fintela -f extra_indexes.sql
   ```

3. Update `.env` with your local PostgreSQL credentials

4. Load CSV:
   ```bash
   uv run python scripts/init_db.py
   ```

5. Start services:
   ```bash
   # FastAPI
   uv run python run_api.py

   # Dagster
   dagster dev
   ```

---
## Design Philosophy & Thinking Process
İlk olarak Dagster dokümantasyonunu baştan sona okudum. Asset yapısı, dependencies, resources nasıl çalışıyor hepsini anlamam gerekti. Sonra README’nin kalan kısmına baktım, benden tam olarak ne istendiğini netleştirdim.

Analitik tarafa geçince, ilk versiyonda portföy riskini tamamen volatility (std) üzerinden hesaplıyordum. Çalışıyordu ama içime pek sinmedi; biraz yüzeysel kalıyordu. Sadece günlük oynaklığa bakmak bana çok tek boyutlu geldi. Vaktim de olduğu için daha mantıklı bir risk modeli kurmak istedim.

Konu üzerinde araştırınca Markowitz ve CAPM ile karşılaştım. CAPM bu proje için baya “overkill” duruyordu (benchmark, beta vs. gerektiriyor), o yüzden onu es geçtim. Ama Markowitz’nin portföy yaklaşımı hoşuma gitti. Komple Markowitz çözmek yerine, elimdeki verilere uygun, daha hafif bir versiyon (Markowitz-lite) uygulayabileceğimi gördüm.

Sonunda risk modelimi şu dört parçadan oluşturdum:

Kovaryans tabanlı portföy volatilitesi (ana risk metriği)

Herfindahl indeksinden türetilmiş konsantrasyon cezası

Maksimum drawdown (portföyün gördüğü en kötü düşüş)

Likidite cezası (market cap + investor count’tan hesapladığım liquidity score)

Bunların hepsini normalize edip ağırlıklandırarak tek bir risk_score ürettim. Böylece risk artık sadece oynaklıktan ibaret olmuyor; portföy dağılımı, düşüş davranışı ve fonların likiditesi de hesaba katılmış oluyor.

Risk tarafını oturttuktan sonra sıra fon performansına geldi. İlk yaptığım yaklaşım çok basitti:
90 günlük cumulative return alıp aynı kategorideki fonlarla kıyaslayıp percentile hesaplıyordum.
Bu çalışıyordu ama bazı problemleri vardı:

Sadece getiriyi ölçmek risk-adjusted değil (yüksek oynak fonlar yanlış şekilde iyi görünüyordu).

Kategoriler bazen çok küçük (3 fon gibi) → percentile güvenilmez.

Outlier fonlar yüzünden dağılım bozuluyordu → yanlış poor-performer alarmı çıkıyordu.

Bunu iyileştirmek için daha mantıklı bir metrik oluşturmaya karar verdim.

Araştırma ve İyileştirme

Markowitz'i risk tarafında kullanmıştım, performans tarafında da Sharpe Ratio mantığına bakmaya başladım. Ama gerçek Sharpe yapmak için risk-free rate vs. gerekiyor. O yüzden daha basit bir şey yaptım:

Yeni Performans Modelim
Her fon için:
90 günlük total_return (bileşik getiri)

90 günlük volatility

sharpe_like = return / volatility

→ Yani “risk başına getiriyi” hesaplamış oldum.

Sonra peer karşılaştırması için biraz daha akıllı bir mantık getirdim:

Önce category içinde kıyasla (yeterince büyükse)

Değilse main_category seviyesine çık

O da olmazsa tüm fonlarla kıyasla (fallback)

Böylece kategori küçükse saçma percentile çıkmıyor.

Ek olarak, outlier’ları düzeltmek için robust bir metrik ekledim:

category içindeki median

MAD (median absolute deviation)

robust z-score

Poor performer işaretlemek için iki koşulu birlikte kullandım:

performance_score ≤ 0.10 (percentile)

z-score ≤ -1.5 (gerçekten akranlarından belirgin şekilde kötü)

Bu ikili sayesinde sistem artık çok daha “temiz” ve spam’siz alert üretiyor.

Sonuç

Yeni model önceki modele göre daha tutarlı:

Yüksek oynak ama şansa iyi getiri yapmış fonlar artık “iyi” görünmüyor.

Çok düşük oynak ama hafif negatif getiri yapan fonlar gereksiz yere kötü görünmüyor.

Poor performer’lar daha az ama daha “gerçek” oluyor.

Fund performance score artık sadece getiriyi değil, risk-adjusted performansı yansıtıyor.
