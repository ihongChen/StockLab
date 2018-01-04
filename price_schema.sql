use external

create table twstock_daily_price(
	靡ㄩ腹 varchar(6),
	yyyymmdd smalldatetime,
 	Θユ秖 	decimal(15,3),
	Θユ掸计 bigint,	
	秨絃基 	decimal(6,2),
	程蔼基 	decimal(6,2),
	程基 	decimal(6,2),
	Μ絃基 	decimal(6,2),
	セ痲ゑ	decimal(6,2)
	CONSTRAINT pk_stock_price PRIMARY KEY(靡ㄩ腹,yyyymmdd)
)

select count(*) from twstock_daily_price

drop table twstock_daily_price