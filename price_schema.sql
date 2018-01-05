use external

create table twstock_daily_price(
	證券代號 varchar(6),
	yyyymmdd smalldatetime,
 	成交量 	decimal(15,3),
	成交筆數 bigint,	
	開盤價 	decimal(6,2),
	最高價 	decimal(6,2),
	最低價 	decimal(6,2),
	收盤價 	decimal(6,2),
	本益比	decimal(6,2)
	CONSTRAINT pk_stock_price PRIMARY KEY(證券代號,yyyymmdd)
)


create table twstock_monthly_revenue(
	公司代號 varchar(10),
	yyyymmdd smalldatetime,
	公司名稱 varchar(20),
	當月營收 decimal(15,1),
	上月營收 decimal(15,1),
	[上月比較增減(%)] decimal(15,2),
	去年當月營收 decimal(15,1),
	[去年同月增減(%)] decimal(15,2),
	當月累計營收 decimal(15,1),
	去年累計營收 decimal(15,1),
	[前期比較增減(%)] decimal(15,2),
	[上市櫃] nvarchar(10),
	CONSTRAINT pk_stock_revenue PRIMARY KEY(公司代號,yyyymmdd)
)
select * from twstock_monthly_revenue
where 公司名稱 
-- select count(*) from twstock_daily_price

drop table twstock_monthly_revenue

