use external

create table twstock_daily_price(
	�Ҩ�N�� varchar(6),
	yyyymmdd smalldatetime,
 	����q 	decimal(15,3),
	���浧�� bigint,	
	�}�L�� 	decimal(6,2),
	�̰��� 	decimal(6,2),
	�̧C�� 	decimal(6,2),
	���L�� 	decimal(6,2),
	���q��	decimal(6,2)
	CONSTRAINT pk_stock_price PRIMARY KEY(�Ҩ�N��,yyyymmdd)
)

select count(*) from twstock_daily_price

drop table twstock_daily_price