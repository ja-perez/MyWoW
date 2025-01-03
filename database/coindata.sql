CREATE DATABASE [coindata]
GO

USE coindata;
GO

CREATE SCHEMA [Coin]
GO

CREATE TABLE [Coin].[DailyPrice] (
    [symbol] VARCHAR(10) NOT NULL,
    [trading_pair] VARCHAR(50) PRIMARY KEY,
    [date] DATETIME NOT NULL,
    [open] FLOAT NOT NULL,
    [high] FLOAT NOT NULL,
    [low] FLOAT NOT NULL,
    [close] FLOAT NOT NULL,
    [volume] FLOAT NOT NULL
)
GO

CREATE TABLE [Coin].[Prediction] (
    [symbol] VARCHAR(10) NOT NULL,
    [trading_pair] VARCHAR(50) NOT NULL,
    [start_date] DATETIME NOT NULL,
    [end_date] DATETIME NOT NULL,
    [start_close] FLOAT NOT NULL,
    [end_close] FLOAT NOT NULL,
    [buy_price] FLOAT DEFAULT 0,
    [sell_price] FLOAT DEFAULT 0,
)
GO

CREATE TABLE [Coin].[PredictionResult] (
    [symbol] VARCHAR(10) NOT NULL,
    [trading_pair] VARCHAR(50) NOT NULL,
    [start_date] DATETIME NOT NULL,
    [end_date] DATETIME NOT NULL,
    [start_close] FLOAT NOT NULL,
    [end_close] FLOAT NOT NULL,
    [buy_price] FLOAT DEFAULT 0,
    [sell_price] FLOAT DEFAULT 0,
    [actual_close] FLOAT NOT NULL,
)
GO

CREATE FUNCTION dbo.GetPredictionSymbols()
RETURNS TABLE
AS
RETURN
(
    SELECT DISTINCT symbol
    FROM Coin.Prediction
)
GO

CREATE FUNCTION dbo.GetPredictionSymbolDates(@symbol VARCHAR(10))
RETURNS TABLE
AS
RETURN
(
    SELECT DISTINCT date
    FROM Coin.Prediction
    WHERE symbol = @symbol
)
GO