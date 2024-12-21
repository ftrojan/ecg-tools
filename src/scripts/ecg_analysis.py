import logging
from data import data
from ecg import ecg


logging.basicConfig(level="INFO", format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
logger.info("started")
logger.info(f"{len(data.c)} companies, {len(data.p2c)} p2c, {len(data.c2c)} c2c")
p2c = ecg.P2C.from_df(data.p2c)
c_owners = p2c.get_owners("C")
logger.info(f"{len(c_owners)} owners of C: {c_owners}")
lc1 = p2c.get_linked_companies_one_level("C")
logger.info(f"{len(lc1)} linked companies one level: {lc1}")
lc = p2c.get_linked_companies("C", levels=3)
logger.info(f"{len(lc)} linked companies two levels: {lc}")
c2c = ecg.C2C.from_df(data.c2c)
pa = c2c.get_parents("C")
logger.info(f"{len(pa)} parents of C: {pa}")
ch = c2c.get_children("C")
logger.info(f"{len(ch)} children of C: {ch}")
an = c2c.get_ancestors("C", levels=3)
logger.info(f"{len(an)} ancestors of C: {an}")
de = c2c.get_descendants("C", levels=3)
logger.info(f"{len(de)} descendants of C: {de}")
bown = ecg.get_beneficial_owners("C", p2c, c2c, levels=3)
logger.info(f"{len(bown)} beneficial owners of C: {bown}")
logger.info(f"checksum of shares: {sum([x.share for x in bown])}")
logger.info("completed")
