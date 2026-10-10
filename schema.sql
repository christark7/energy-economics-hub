DROP TABLE IF EXISTS market_spread_opportunities;
DROP TABLE IF EXISTS market_observations;

CREATE TABLE market_observations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    source NVARCHAR(100),
    market NVARCHAR(100),
    company NVARCHAR(100),
    region NVARCHAR(100),
    commodity NVARCHAR(100),
    timestamp DATETIME2,
    price_value FLOAT,
    currency NVARCHAR(10),
    unit NVARCHAR(50),
    is_stale BIT,
    created_at DATETIME2 DEFAULT GETDATE()
);

CREATE TABLE market_spread_opportunities (
    id INT IDENTITY(1,1) PRIMARY KEY,
    market NVARCHAR(100),
    region NVARCHAR(100),
    commodity NVARCHAR(100),
    timestamp DATETIME2,
    buy_source NVARCHAR(100),
    sell_source NVARCHAR(100),
    gross_spread FLOAT,
    currency NVARCHAR(10),
    unit NVARCHAR(50),
    created_at DATETIME2 DEFAULT GETDATE()
);