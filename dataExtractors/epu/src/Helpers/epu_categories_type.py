from enum import Enum


class EPUCategoriesType(Enum):
    """Class to define the types of EPU categories."""
    
    NONE = "none"
    TRADE = "trade"
    CURRENCY_CRISIS = "currency_crisis"
    FISCAL = "fiscal"
    MONETARY_POLICY = "monetary_policy"