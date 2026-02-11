from enum import Enum


class CategoryEnum(str, Enum):
    DINING = "餐飲"
    DAILY = "日用品"
    TRANSPORT = "交通"
    HOUSING = "居住"
    ENTERTAINMENT = "娛樂"
    CLOTHING = "服飾"
    MEDICAL = "醫療"
    EDUCATION = "教育"
    WORK = "工作"
    SOCIAL = "社交"
    PET = "寵物"
    OTHER = "其他"


VALID_CATEGORIES = [c.value for c in CategoryEnum]
