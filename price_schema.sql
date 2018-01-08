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


create table twstock_monthly_revenue(
	���q�N�� varchar(10),
	yyyymmdd smalldatetime,
	���q�W�� varchar(20),
	����禬 decimal(15,1),
	�W���禬 decimal(15,1),
	[�W�����W��(%)] decimal(15,2),
	�h�~����禬 decimal(15,1),
	[�h�~�P��W��(%)] decimal(15,2),
	���֭p�禬 decimal(15,1),
	�h�~�֭p�禬 decimal(15,1),
	[�e������W��(%)] decimal(15,2),
	[�W���d] nvarchar(10),
	CONSTRAINT pk_stock_revenue PRIMARY KEY(���q�N��,yyyymmdd)
)
select * from twstock_monthly_revenue
where ���q�W�� 
-- select count(*) from twstock_daily_price

drop table twstock_monthly_revenue

