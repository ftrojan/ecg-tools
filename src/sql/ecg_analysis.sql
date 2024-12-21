create temporary table c as
    select * from (
    values
        ('C', 100),
        ('C1', 400),
        ('C2', 1000),
        ('C3', 500),
        ('C4', 10),
        ('C5', 100),
        ('C6', 500),
        ('C7', 200),
        ('C8', 20)
) as t (company, turnover);

create temporary table p2c as
    select * from (
    values
        ('P1', 'C', 0.2),
        ('P2', 'C', 0.3),
        ('P2', 'C1', 0.1),
        ('P3', 'C2', 0.8),
        ('P4', 'C1', 0.9),
        ('P4', 'C2', 0.2),
        ('P4', 'C3', 0.5),
        ('P4', 'C4', 0.5),
        ('P4', 'C5', 0.1),
        ('P5', 'C8', 1.0),
        ('P5', 'C7', 0.6)
) as t (person, company, share);

create temporary table c2c as
    select * from (
    values
        ('C1', 'C', 0.25),
        ('C2', 'C', 0.15),
        ('C3', 'C', 0.10),
        ('C8', 'C3', 0.50),
        ('C', 'C4', 0.50),
        ('C', 'C5', 0.90),
        ('C4', 'C6', 1.00),
        ('C4', 'C7', 0.40)
) as t (c1, c2, share);

-- n_owners for C
select person as owner
from p2c
where company = 'C';

-- n_companies_owner_linked_curr, turnover_owner_linked_czk
select a.company, b.person, b.company company_owner_linked, c.turnover
from p2c a
inner join p2c b on b.person = a.person and b.company <> a.company
inner join c on b.company = c.company
where a.company = 'C';

-- parent companies
select c1, share
from c2c
where c2 = 'C';

-- grandparent companies
select t1.c1, t1.share share1, t2.c1 as c2, t2.share share2
from c2c t1
inner join c2c t2 on t1.c1 = t2.c2
where t1.c2 = 'C'
;

-- level 2 owners and their share
select t1.c1, t1.share share1, t2.person, t2.share share2, t1.share * t2.share prod_share
from c2c t1
inner join p2c t2 on t2.company = t1.c1
where t1.c2 = 'C';

-- level 3 owners
select t1.c1, t1.share share1, t2.c1 as c2, t2.share share2, t3.person, t3.share share3
    , t1.share * t2.share * t3.share as prod_share
from c2c t1
inner join c2c t2 on t1.c1 = t2.c2
inner join p2c t3 on t3.company = t2.c1
where t1.c2 = 'C'
;

-- child companies - level 1
select t1.c1 as c0
    , c0.turnover as t0
    , t1.c2 as c1
    , c1.turnover as t1
    , t1.share as s1
    , c1.turnover * t1.share as child_turnover_1
from c2c t1
inner join c c0 on c0.company = t1.c1
inner join c c1 on c1.company = t1.c2
where t1.c1 = 'C';

-- child companies - level 2
select t1.c1 as c0
     , c0.turnover t0
     , t1.c2 as c1
     , c1.turnover t1
     , t1.share s1
     , t2.c2 as c2
     , c2.turnover as t2
     , t2.share s2
     , t1.share * c2.turnover * t2.share as child_turnover_2
from c2c t1
inner join c2c t2 on t1.c2 = t2.c1
inner join c c0 on c0.company = t1.c1
inner join c c1 on c1.company = t2.c1
inner join c c2 on c2.company = t2.c2
where t1.c1 = 'C';
