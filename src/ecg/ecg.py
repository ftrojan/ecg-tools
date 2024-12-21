import logging
from dataclasses import dataclass
import math
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Ownership:

    person: str
    company: str
    share: float

    def __repr__(self) -> str:
        s = f"{self.person}>{self.share}>{self.company}"
        return s


@dataclass(frozen=True)
class SameOwner:

    person: str
    c1: str
    share1: float
    c2: str
    share2: float

    def __repr__(self):
        s = f"{self.c1}<{self.person}>{self.c2}"
        return s


@dataclass(frozen=True)
class LinkedCompany:

    company: str
    link: list[SameOwner]

    def link_key(self):
        return ",".join([str(x) for x in self.link])

    def __key(self) -> tuple[str, str]:
        return self.company, self.link_key()

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, LinkedCompany):
            return self.__key() == other.__key()
        else:
            return False

    def __repr__(self):
        s = f"{self.company} via {self.link_key()}"
        return s


@dataclass(frozen=True)
class P2C:

    ownerships: set[Ownership]
    persons: set[str]
    companies: set[str]
    p2c: dict[str, set[Ownership]]
    c2p: dict[str, set[Ownership]]

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> "P2C":
        own = {
            Ownership(person=x["person"], company=x["company"], share=x["share"])
            for i, x in df.iterrows()
        }
        pers = {x.person for x in own}
        comp = {x.company for x in own}
        p2c = {p: {x for x in own if x.person == p} for p in pers}
        c2p = {c: {x for x in own if x.company == c} for c in comp}
        logger.info(f"{len(own)} ownerships for {len(pers)} persons and {len(comp)} companies.")
        result = cls(
            ownerships=own,
            persons=pers,
            companies=comp,
            p2c=p2c,
            c2p=c2p,
        )
        return result

    def get_owners(self, c: str) -> set[Ownership]:
        return self.c2p.get(c, set())

    def get_owned_companies(self, p: str) -> set[Ownership]:
        return self.p2c.get(p, set())

    def get_linked_companies_one_level(self, c: str) -> set[LinkedCompany]:
        c2p_ownerships = self.get_owners(c)
        result = {
            LinkedCompany(
                company=x2.company,
                link=[SameOwner(person=x1.person, c1=c, share1=x1.share, c2=x2.company, share2=x2.share)]
            )
            for x1 in c2p_ownerships
            for x2 in self.get_owned_companies(x1.person)
            if x2.company != c
        }
        return result

    def get_linked_companies(self, c: str, levels: int) -> set[LinkedCompany]:
        linked_companies = self.get_linked_companies_one_level(c)
        unique_linked = {c} | {c.company for c in linked_companies}
        n_added = len(linked_companies)
        for level in range(2, levels+1):
            linked_companies_level = {
                LinkedCompany(link.company, cx.link + link.link)
                for cx in linked_companies
                for link in self.get_linked_companies_one_level(cx.company)
                if link.company not in unique_linked
            }
            linked_companies |= linked_companies_level
            unique_linked |= {c.company for c in linked_companies_level}
            n_added = len(linked_companies_level)
        if n_added > 0:
            logger.warning(f"{n_added=} linked companies in level {levels}. Consider increasing levels.")
        return linked_companies


@dataclass(frozen=True)
class Parentship:
    c1: str
    c2: str
    share: float

    def __repr__(self):
        s = f"{self.c1}>{self.share:.3f}>{self.c2}"
        return s


@dataclass(frozen=True)
class Ancestor:

    company: str
    link: list[Parentship]

    def link_key(self):
        return ",".join([str(x) for x in self.link])

    def __key(self) -> tuple[str, str]:
        return self.company, self.link_key()

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, Ancestor):
            return self.__key() == other.__key()
        else:
            return False

    def __repr__(self):
        s = f"{self.company} via {self.link_key()}"
        return s


@dataclass(frozen=True)
class C2C:

    parentships: set[Parentship]
    parents: set[str]
    childs: set[str]
    companies: set[str]
    pa2ch: dict[str, set[Parentship]]
    ch2pa: dict[str, set[Parentship]]

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> "C2C":
        pas = {
            Parentship(c1=x["c1"], c2=x["c2"], share=x["share"])
            for i, x in df.iterrows()
        }
        ps = {x.c1 for x in pas}
        cs = {x.c2 for x in pas}
        comp = ps | cs
        p2c = {p: {x for x in pas if x.c1 == p} for p in ps}
        c2p = {c: {x for x in pas if x.c2 == c} for c in cs}
        logger.info(f"{len(pas)} parentships among {len(comp)} companies.")
        result = cls(
            parentships=pas,
            parents=ps,
            childs=cs,
            companies=comp,
            pa2ch=p2c,
            ch2pa=c2p,
        )
        return result

    def get_parents(self, c: str) -> set[Parentship]:
        return self.ch2pa.get(c, set())

    def get_children(self, c: str) -> set[Parentship]:
        return self.pa2ch.get(c, set())

    def get_ancestors(self, c: str, levels: int) -> set[Ancestor]:
        ancestors = {
            Ancestor(company=x.c1, link=[x])
            for x in self.get_parents(c)
        }
        used_companies = {c} | {a.company for a in ancestors}
        n_added = len(used_companies) - 1
        for level in range(2, levels+1):
            ancestors_level = {
                Ancestor(company=a2.c1, link=a1.link + [a2])
                for a1 in ancestors
                for a2 in self.get_parents(a1.company)
                if a2.c1 not in used_companies
            }
            used_companies_level = {a.company for a in ancestors_level}
            ancestors |= ancestors_level
            used_companies |= used_companies_level
            n_added = len(used_companies_level)
        if n_added > 0:
            logger.warning(f"{n_added=} ancestors of {c} in level {levels}. Consider increasing levels.")
        return ancestors

    def get_descendants(self, c: str, levels: int) -> set[Ancestor]:
        descendants = {
            Ancestor(company=x.c2, link=[x])
            for x in self.get_children(c)
        }
        used_companies = {c} | {d.company for d in descendants}
        n_added = len(used_companies) - 1
        for level in range(2, levels+1):
            descendants_level = {
                Ancestor(company=d2.c2, link=d1.link + [d2])
                for d1 in descendants
                for d2 in self.get_children(d1.company)
                if d2.c2 not in used_companies
            }
            used_companies_level = {d.company for d in descendants_level}
            descendants |= descendants_level
            used_companies |= used_companies_level
            n_added = len(used_companies_level)
        if n_added > 0:
            logger.warning(f"{n_added=} descendants of {c} in level {levels}. Consider increasing levels.")
        return descendants


@dataclass(frozen=True)
class OwnershipPath:
    """Path of person owning a company through sequence of [Ownership, Parentship, ..., Parentship]."""

    p2c_ownership: Ownership
    c2c_parentships: list[Parentship]

    def c2c_key(self):
        return ",".join([str(x) for x in self.c2c_parentships])

    def __key(self) -> tuple[Ownership, str]:
        return self.p2c_ownership, self.c2c_key()

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other) -> bool:
        if isinstance(other, OwnershipPath):
            return self.__key() == other.__key()
        else:
            return False

    def __repr__(self):
        s = f"{self.p2c_ownership}{self.c2c_key()}"
        return s

    def final_share(self) -> float:
        """Returns final share as a product of all shares along the path."""
        shs = [self.p2c_ownership.share] + [p.share for p in self.c2c_parentships]
        sh = math.prod(shs)
        return sh


@dataclass
class ChainedOwnership:
    """A person owns a company through one or many paths."""

    person: str
    company: str
    share: float
    paths: set[OwnershipPath]

    def __repr__(self) -> str:
        s = f"{self.person}>{self.share}>{self.company} via {len(self.paths)} paths {self.paths}"
        return s

    def __lt__(self, other: "ChainedOwnership") -> bool:
        return self.share < other.share


def calc_final_share(paths: set[OwnershipPath]) -> float:
    """Returns the final share as the sum of shares across the paths."""
    final_share = sum([p.final_share() for p in paths])
    return final_share


def get_beneficial_owners(c: str, p2c: P2C, c2c: C2C, levels: int) -> list[ChainedOwnership]:
    """Calculate all beneficial owners of a company."""
    direct_ownerships = {
        x.person: ChainedOwnership(
            person=x.person,
            company=c,
            share=x.share,
            paths={OwnershipPath(p2c_ownership=x, c2c_parentships=[])},
        )
        for x in p2c.get_owners(c)
    }
    ancestors: set[Ancestor] = c2c.get_ancestors(c, levels)
    anc_companies = {a.company for a in ancestors}
    ownerships: dict[str, ChainedOwnership] = direct_ownerships
    for anc_company in anc_companies:
        anc_owners: set[Ownership] = p2c.get_owners(anc_company)
        anc_paths: set[Ancestor] = {a for a in ancestors if a.company == anc_company}
        for anc_owner in anc_owners:  # type: Ownership
            paths = {
                OwnershipPath(
                    p2c_ownership=anc_owner,
                    c2c_parentships=ap.link,
                )
                for ap in anc_paths
            }
            if anc_owner.person in ownerships:
                paths = ownerships[anc_owner.person].paths | paths
            share = calc_final_share(paths)
            ownership = ChainedOwnership(
                person=anc_owner.person,
                company=c,
                share=share,
                paths=paths,
            )
            ownerships[anc_owner.person] = ownership
    sorted_ownerships = sorted(ownerships.values(), reverse=True)
    return sorted_ownerships
