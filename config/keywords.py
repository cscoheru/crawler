"""
Keyword rules for content classification.
"""

# Category keywords with weights (0.0-1.0)
KEYWORD_RULES = {
    "psychology": {
        "name": "心理咨询",
        "keywords": {
            # Core terms (high weight)
            "心理咨询": 1.0,
            "心理治疗": 1.0,
            "心理辅导": 1.0,
            "心理咨询师": 1.0,

            # Disorders (high weight)
            "抑郁症": 0.95,
            "焦虑症": 0.95,
            "强迫症": 0.95,
            "恐惧症": 0.95,
            "双相情感障碍": 0.95,
            "失眠症": 0.9,
            "心理障碍": 0.9,

            # Therapies (medium weight)
            "认知行为疗法": 0.85,
            "精神分析": 0.85,
            "心理动力学": 0.8,
            "团体治疗": 0.8,
            "家庭治疗": 0.8,
            "艺术治疗": 0.75,

            # General terms (lower weight)
            "心理健康": 0.7,
            "情绪管理": 0.7,
            "压力缓解": 0.7,
            "心理问题": 0.7,
            "心理状态": 0.65,
            "心理": 0.5,
            "抑郁": 0.6,
            "焦虑": 0.6,
            "情绪": 0.5,
        }
    },
    "management": {
        "name": "企业管理",
        "keywords": {
            # Core terms (high weight)
            "企业管理": 1.0,
            "管理学": 1.0,
            "CEO": 0.95,
            "总经理": 0.9,
            "高管": 0.85,

            # Strategy (high weight)
            "战略管理": 1.0,
            "企业战略": 0.95,
            "商业模式": 0.9,
            "竞争战略": 0.85,
            "战略规划": 0.85,

            # Leadership (medium-high weight)
            "领导力": 0.95,
            "团队建设": 0.9,
            "领导艺术": 0.85,
            "执行力": 0.8,

            # HR and organization (medium weight)
            "人力资源管理": 0.9,
            "组织管理": 0.85,
            "绩效管理": 0.85,
            "企业文化": 0.8,
            "组织架构": 0.8,
            "员工激励": 0.75,
            "人才管理": 0.75,
            "团队协作": 0.7,

            # Project and operations (medium weight)
            "项目管理": 0.85,
            "运营管理": 0.8,
            "流程优化": 0.75,
            "效率提升": 0.7,

            # General terms (lower weight)
            "管理": 0.5,
            "团队": 0.5,
            "公司": 0.4,
            "企业": 0.4,
        }
    },
    "finance": {
        "name": "财务会计税务",
        "keywords": {
            # Core terms (high weight)
            "会计": 1.0,
            "注册会计师": 1.0,
            "CPA": 0.95,
            "会计师": 0.9,

            # Tax (high weight)
            "税务": 1.0,
            "税务筹划": 0.95,
            "报税": 0.9,
            "税收": 0.85,
            "增值税": 0.85,
            "企业所得税": 0.85,
            "个人所得税": 0.8,
            "税务申报": 0.8,

            # Finance (medium-high weight)
            "财务管理": 0.9,
            "财务分析": 0.85,
            "财务报表": 0.85,
            "财务总监": 0.85,
            "CFO": 0.85,
            "预算管理": 0.8,

            # Accounting types (medium weight)
            "财务会计": 0.9,
            "管理会计": 0.85,
            "成本会计": 0.8,
            "审计": 0.85,
            "内部审计": 0.8,
            "外部审计": 0.75,

            # Standards and regulations (medium weight)
            "会计准则": 0.8,
            "会计制度": 0.75,
            "会计核算": 0.75,
            "财务制度": 0.7,

            # Specific items (medium-low weight)
            "资产负债表": 0.75,
            "利润表": 0.75,
            "现金流量表": 0.7,
            "应收账款": 0.65,
            "应付账款": 0.65,
            "成本核算": 0.7,

            # General terms (lower weight)
            "财务": 0.5,
            "账务": 0.5,
            "记账": 0.5,
            "核算": 0.5,
        }
    }
}

# Exclusion keywords (content with these should be flagged or excluded)
EXCLUSION_KEYWORDS = {
    "spam": [
        "加微信", "联系QQ", "代写", "刷单", "贷款", "彩票",
        "博彩", "赌博", "投资理财", "内幕消息", "涨停板",
        "股票推荐", "快速致富", "暴利", "兼职刷单"
    ],
    "advertisement": [
        "立即购买", "限时优惠", "促销", "折扣", "优惠券",
        "点击购买", "免费试用", "专柜价", "原价", "现价"
    ]
}

# Category mapping for export
CATEGORY_MAPPING = {
    "psychology": "心理咨询",
    "management": "企业管理",
    "finance": "财务会计税务",
    "other": "其他"
}
