"""
Multi-level category taxonomy with detailed subcategories.
"""

# Category taxonomy definition
CATEGORY_TAXONOMY = {
    "psychology": {
        "name": "心理咨询",
        "subcategories": {
            "clinical": {
                "name": "临床心理",
                "sub_subcategories": {
                    "depression": {"name": "抑郁障碍", "keywords": ["抑郁症", "抑郁发作", "重度抑郁", "轻度抑郁", "双相抑郁"]},
                    "anxiety": {"name": "焦虑障碍", "keywords": ["焦虑症", "广泛性焦虑", "惊恐发作", "恐惧症", "强迫症"]},
                    "obsessive_compulsive": {"name": "强迫障碍", "keywords": ["强迫症", "强迫行为", "强迫思维", "OCD"]},
                    "phobia": {"name": "恐惧症", "keywords": ["恐惧症", "社交恐惧", "广场恐惧", "特定恐惧"]},
                    "bipolar": {"name": "双相障碍", "keywords": ["双相情感障碍", "躁郁症", "躁狂发作", "双相"]},
                    "insomnia": {"name": "睡眠障碍", "keywords": ["失眠症", "睡眠障碍", "嗜睡症", "睡眠呼吸暂停"]},
                    "eating_disorder": {"name": "进食障碍", "keywords": ["厌食症", "贪食症", "暴食症", "进食障碍"]},
                    "ptsd": {"name": "创伤应激", "keywords": ["PTSD", "创伤后应激障碍", "急性应激障碍", "创伤"]},
                }
            },
            "therapy": {
                "name": "咨询技术",
                "sub_subcategories": {
                    "cbt": {"name": "认知行为疗法", "keywords": ["认知行为疗法", "CBT", "认知重构", "行为激活", "暴露疗法"]},
                    "psychodynamic": {"name": "精神分析", "keywords": ["精神分析", "心理动力学", "移情", "反移情", "自由联想"]},
                    "person_centered": {"name": "人本主义", "keywords": ["人本主义", "当事人中心", "罗杰斯", "无条件积极关注"]},
                    "family_therapy": {"name": "家庭治疗", "keywords": ["家庭治疗", "夫妻治疗", "婚姻治疗", "系统式家庭治疗"]},
                    "art_therapy": {"name": "艺术治疗", "keywords": ["艺术治疗", "音乐治疗", "绘画治疗", "沙盘治疗", "表达性艺术治疗"]},
                    "group_therapy": {"name": "团体治疗", "keywords": ["团体治疗", "小组治疗", "团体辅导", "心理剧"]},
                }
            },
            "developmental": {
                "name": "发展心理",
                "sub_subcategories": {
                    "child": {"name": "儿童心理", "keywords": ["儿童心理", "儿童发展", "幼儿心理", "儿童行为问题"]},
                    "adolescent": {"name": "青少年心理", "keywords": ["青少年心理", "青春期", "叛逆期", "青少年问题"]},
                    "adult": {"name": "成年心理", "keywords": ["成年心理", "中年危机", "成年发展"]},
                    "elderly": {"name": "老年心理", "keywords": ["老年心理", "老龄化", "老年抑郁", "认知障碍"]},
                }
            },
            "relationship": {
                "name": "婚恋家庭",
                "sub_subcategories": {
                    "marriage": {"name": "婚姻咨询", "keywords": ["婚姻咨询", "夫妻关系", "婚姻危机", "婚姻经营"]},
                    "dating": {"name": "恋爱心理", "keywords": ["恋爱心理", "情感关系", "约会技巧", "亲密关系"]},
                    "family": {"name": "家庭关系", "keywords": ["家庭关系", "亲子关系", "婆媳关系", "家庭沟通"]},
                    "divorce": {"name": "离婚心理", "keywords": ["离婚心理", "离异", "离婚调适", "单亲家庭"]},
                }
            },
            "workplace": {
                "name": "职场心理",
                "sub_subcategories": {
                    "career": {"name": "职业规划", "keywords": ["职业规划", "职业发展", "职业选择", "转行"]},
                    "work_stress": {"name": "工作压力", "keywords": ["工作压力", "职业倦怠", "过劳", "压力管理"]},
                    "leadership_psych": {"name": "领导力心理", "keywords": ["领导力心理", "管理心理", "决策心理", "影响力"]},
                    "workplace_conflict": {"name": "职场人际", "keywords": ["职场人际", "同事关系", "职场沟通", "职场霸凌"]},
                }
            },
            "emotion": {
                "name": "情绪管理",
                "sub_subcategories": {
                    "emotion_regulation": {"name": "情绪调节", "keywords": ["情绪调节", "情绪管理", "情绪控制", "情商"]},
                    "anger": {"name": "愤怒管理", "keywords": ["愤怒管理", "控制愤怒", "情绪宣泄"]},
                    "stress": {"name": "压力管理", "keywords": ["压力管理", "减压", "应对压力", "心理压力"]},
                    "resilience": {"name": "心理韧性", "keywords": ["心理韧性", "抗逆力", "复原力", "心理资本"]},
                }
            },
        }
    },
    "management": {
        "name": "企业管理",
        "subcategories": {
            "strategy": {
                "name": "战略管理",
                "sub_subcategories": {
                    "corporate_strategy": {"name": "企业战略", "keywords": ["企业战略", "公司战略", "战略规划", "战略目标"]},
                    "business_strategy": {"name": "业务战略", "keywords": ["业务战略", "竞争战略", "差异化战略", "成本领先"]},
                    "blue_ocean": {"name": "蓝海战略", "keywords": ["蓝海战略", "价值创新", "红海", "市场创新"]},
                    "strategic_analysis": {"name": "战略分析", "keywords": ["SWOT分析", "PEST分析", "波特五力", "战略分析"]},
                    "strategic_execution": {"name": "战略执行", "keywords": ["战略执行", "战略落地", "战略实施", "执行"]},
                }
            },
            "hr": {
                "name": "人力资源",
                "sub_subcategories": {
                    "hr_planning": {"name": "人力资源规划", "keywords": ["人力资源规划", "人力规划", "人才规划", "HR规划"]},
                    "organization": {"name": "组织架构", "keywords": ["组织架构", "组织设计", "组织结构", "扁平化", "矩阵式"]},
                    "position_system": {"name": "职位体系", "keywords": ["职位体系", "岗位体系", "职位描述", "岗位分析", "胜任力模型"]},
                    "compensation_benefits": {"name": "薪酬绩效", "keywords": ["薪酬管理", "绩效管理", "薪酬体系", "绩效考核", "KPI", "OKR", "股权激励"]},
                    "talent_management": {"name": "人才管理", "keywords": ["人才管理", "人才发展", "人才盘点", "继任计划", "人才梯队"]},
                    "recruitment": {"name": "招聘选拔", "keywords": ["招聘", "选拔", "面试", "人才引进", "校园招聘", "猎头"]},
                    "training": {"name": "培训发展", "keywords": ["培训", "员工发展", "学习发展", "企业大学", "培训体系"]},
                    "employee_relations": {"name": "员工关系", "keywords": ["员工关系", "劳动关系", "员工满意", "员工敬业度"]},
                }
            },
            "culture": {
                "name": "企业文化",
                "sub_subcategories": {
                    "culture_building": {"name": "文化建设", "keywords": ["企业文化建设", "文化落地", "文化塑造", "价值观"]},
                    "culture_transformation": {"name": "文化变革", "keywords": ["文化变革", "文化转型", "组织变革", "变革管理"]},
                    "employer_brand": {"name": "雇主品牌", "keywords": ["雇主品牌", "最佳雇主", "雇主形象", "员工体验"]},
                    "org_behavior": {"name": "组织行为", "keywords": ["组织行为", "行为管理", "员工行为", "组织氛围"]},
                }
            },
            "operations": {
                "name": "运营管理",
                "sub_subcategories": {
                    "supply_chain": {"name": "供应链管理", "keywords": ["供应链管理", "供应链", "采购管理", "物流管理", "供应商管理"]},
                    "process_optimization": {"name": "流程优化", "keywords": ["流程优化", "业务流程", "流程再造", "BPR", "精益管理"]},
                    "quality_control": {"name": "质量管理", "keywords": ["质量管理", "质量控制", "六西格玛", "QA", "QC"]},
                    "project_management": {"name": "项目管理", "keywords": ["项目管理", "敏捷开发", "Scrum", "项目控制", "PM"]},
                    "lean_production": {"name": "精益生产", "keywords": ["精益生产", "精益管理", "5S", "TPS", "丰田生产方式"]},
                }
            },
            "marketing": {
                "name": "市场营销",
                "sub_subcategories": {
                    "brand_management": {"name": "品牌管理", "keywords": ["品牌管理", "品牌建设", "品牌策略", "品牌定位"]},
                    "digital_marketing": {"name": "数字营销", "keywords": ["数字营销", "网络营销", "新媒体营销", "社交媒体营销"]},
                    "market_research": {"name": "市场调研", "keywords": ["市场调研", "市场研究", "用户调研", "消费者洞察"]},
                    "product_marketing": {"name": "产品营销", "keywords": ["产品营销", "产品策略", "产品定位", "产品生命周期"]},
                    "customer_strategy": {"name": "客户策略", "keywords": ["客户关系", "CRM", "客户运营", "用户增长", "私域流量"]},
                    "sales_management": {"name": "销售管理", "keywords": ["销售管理", "销售技巧", "渠道管理", "销售团队"]},
                }
            },
            "innovation": {
                "name": "创新管理",
                "sub_subcategories": {
                    "product_innovation": {"name": "产品创新", "keywords": ["产品创新", "产品研发", "R&D", "研发管理"]},
                    "business_model": {"name": "商业模式", "keywords": ["商业模式", "商业创新", "盈利模式", "平台模式"]},
                    "digital_transformation": {"name": "数字化转型", "keywords": ["数字化转型", "数字化", "信息化", "企业数字化"]},
                    "open_innovation": {"name": "开放式创新", "keywords": ["开放式创新", "协同创新", "生态创新"]},
                }
            },
            "leadership": {
                "name": "领导力发展",
                "sub_subcategories": {
                    "executive_leadership": {"name": "高管领导力", "keywords": ["CEO", "高管", "高管团队", "决策层", "董事会"]},
                    "middle_management": {"name": "中层管理", "keywords": ["中层管理", "部门经理", "团队主管", "管理技能"]},
                    "leadership_dev": {"name": "领导力发展", "keywords": ["领导力发展", "领导力培养", "领导梯队", "潜能开发"]},
                    "decision_making": {"name": "决策管理", "keywords": ["决策管理", "决策方法", "科学决策", "数据决策"]},
                }
            },
        }
    },
    "finance": {
        "name": "财务会计税务",
        "subcategories": {
            "financial_accounting": {
                "name": "财务会计",
                "sub_subcategories": {
                    "accounting_standards": {"name": "会计准则", "keywords": ["会计准则", "企业会计准则", "IAS", "IFRS", "GAAP"]},
                    "financial_statements": {"name": "财务报表", "keywords": ["财务报表", "资产负债表", "利润表", "现金流量表", "所有者权益变动表"]},
                    "accounting_cycle": {"name": "会计核算", "keywords": ["会计核算", "记账", "凭证", "账簿", "会计分录"]},
                    "accounting_systems": {"name": "会计制度", "keywords": ["会计制度", "财务制度", "内控制度", "会计政策"]},
                }
            },
            "management_accounting": {
                "name": "管理会计",
                "sub_subcategories": {
                    "cost_accounting": {"name": "成本会计", "keywords": ["成本会计", "成本核算", "成本控制", "标准成本", "作业成本"]},
                    "budget_management": {"name": "预算管理", "keywords": ["预算管理", "全面预算", "预算编制", "预算执行", "预算考核"]},
                    "performance_measurement": {"name": "绩效管理", "keywords": ["绩效管理", "绩效评价", "KPI", "平衡计分卡", "责任会计"]},
                    "internal_control": {"name": "内部控制", "keywords": ["内部控制", "风险管理", "COSO", "风险控制", "合规管理"]},
                }
            },
            "tax": {
                "name": "税务",
                "sub_subcategories": {
                    "vat": {"name": "增值税", "keywords": ["增值税", "进项税", "销项税", "增值税专用发票", "小规模纳税人"]},
                    "corporate_tax": {"name": "企业所得税", "keywords": ["企业所得税", "企业税收", "汇算清缴", "应纳税所得额"]},
                    "personal_tax": {"name": "个人所得税", "keywords": ["个人所得税", "个税", "专项扣除", "工资薪金"]},
                    "tax_planning": {"name": "税务筹划", "keywords": ["税务筹划", "税收筹划", "节税", "合理避税"]},
                    "tax_compliance": {"name": "税务申报", "keywords": ["税务申报", "报税", "纳税申报", "电子税务局"]},
                    "other_taxes": {"name": "其他税种", "keywords": ["印花税", "城建税", "教育费附加", "土地增值税", "房产税", "契税"]},
                }
            },
            "audit": {
                "name": "审计",
                "sub_subcategories": {
                    "external_audit": {"name": "外部审计", "keywords": ["外部审计", "年报审计", "审计报告", "审计意见"]},
                    "internal_audit": {"name": "内部审计", "keywords": ["内部审计", "内审", "审计部门", "审计程序"]},
                    "audit_standards": {"name": "审计准则", "keywords": ["审计准则", "审计标准", "ISA", "审计规范"]},
                }
            },
            "financial_management": {
                "name": "财务管理",
                "sub_subcategories": {
                    "financial_analysis": {"name": "财务分析", "keywords": ["财务分析", "财务比率", "杜邦分析", "财务指标", "盈利能力"]},
                    "investment_decision": {"name": "投资决策", "keywords": ["投资决策", "资本预算", "NPV", "IRR", "投资回报"]},
                    "financing": {"name": "融资管理", "keywords": ["融资", "股权融资", "债权融资", "IPO", "私募融资"]},
                    "working_capital": {"name": "营运资金", "keywords": ["营运资金", "流动资金", "现金流管理", "资金管理"]},
                    "cfo_role": {"name": "财务总监", "keywords": ["CFO", "财务总监", "首席财务官", "财务高管"]},
                }
            },
            "financial_report": {
                "name": "财务报告",
                "sub_subcategories": {
                    "report_disclosure": {"name": "信息披露", "keywords": ["信息披露", "定期报告", "临时公告", "证监会"]},
                    "consolidated_statements": {"name": "合并报表", "keywords": ["合并报表", "合并财务报表", "母公司", "子公司"]},
                    "segment_reporting": {"name": "分部报告", "keywords": ["分部报告", "业务分部", "地区分部"]},
                }
            },
        }
    }
}


def get_category_path(category_key: str, subcategory_key: str = None, sub_subcategory_key: str = None) -> list:
    """
    Get the full category path as a list.

    Args:
        category_key: Top-level category key
        subcategory_key: Subcategory key (optional)
        sub_subcategory_key: Sub-subcategory key (optional)

    Returns:
        List of category names in hierarchical order
    """
    path = []

    if category_key in CATEGORY_TAXONOMY:
        category = CATEGORY_TAXONOMY[category_key]
        path.append(category["name"])

        if subcategory_key and subcategory_key in category["subcategories"]:
            subcategory = category["subcategories"][subcategory_key]
            path.append(subcategory["name"])

            if sub_subcategory_key and sub_subcategory_key in subcategory["sub_subcategories"]:
                sub_sub = subcategory["sub_subcategories"][sub_subcategory_key]
                path.append(sub_sub["name"])

    return path


def get_all_subcategories(category_key: str) -> dict:
    """Get all subcategories for a given category."""
    if category_key in CATEGORY_TAXONOMY:
        return CATEGORY_TAXONOMY[category_key]["subcategories"]
    return {}


def get_all_sub_subcategories(category_key: str, subcategory_key: str) -> dict:
    """Get all sub-subcategories for a given subcategory."""
    subcategories = get_all_subcategories(category_key)
    if subcategory_key in subcategories:
        return subcategories[subcategory_key]["sub_subcategories"]
    return {}


def flatten_taxonomy() -> dict:
    """
    Flatten taxonomy into a single level with all keywords.

    Returns:
        Dictionary mapping sub-subcategory keys to their metadata
    """
    flat = {}

    for cat_key, cat_data in CATEGORY_TAXONOMY.items():
        for sub_key, sub_data in cat_data["subcategories"].items():
            for sub_sub_key, sub_sub_data in sub_data["sub_subcategories"].items():
                # Create unique key
                unique_key = f"{cat_key}_{sub_key}_{sub_sub_key}"

                flat[unique_key] = {
                    "category": cat_key,
                    "subcategory": sub_key,
                    "sub_subcategory": sub_sub_key,
                    "name": sub_sub_data["name"],
                    "keywords": sub_sub_data["keywords"],
                    "full_path": get_category_path(cat_key, sub_key, sub_sub_key)
                }

    return flat


def get_keywords_for_level(category_key: str = None, subcategory_key: str = None, sub_subcategory_key: str = None) -> list:
    """
    Get keywords for a specific taxonomy level.

    Args:
        category_key: Category key
        subcategory_key: Subcategory key (optional)
        sub_subcategory_key: Sub-subcategory key (optional)

    Returns:
        List of keywords at that level
    """
    keywords = []

    if sub_subcategory_key:
        # Get keywords for specific sub-subcategory
        if category_key and subcategory_key:
            sub_subs = get_all_sub_subcategories(category_key, subcategory_key)
            if sub_subcategory_key in sub_subs:
                keywords = sub_subs[sub_subcategory_key]["keywords"]

    elif subcategory_key:
        # Get all keywords for a subcategory (combine all sub-sub)
        sub_subs = get_all_sub_subcategories(category_key, subcategory_key)
        for sub_sub_data in sub_subs.values():
            keywords.extend(sub_sub_data["keywords"])

    elif category_key:
        # Get all keywords for a category (combine all levels)
        subcategories = get_all_subcategories(category_key)
        for sub_data in subcategories.values():
            for sub_sub_data in sub_data["sub_subcategories"].values():
                keywords.extend(sub_sub_data["keywords"])

    return keywords


# Legacy compatibility - maintain old KEYWORD_RULES structure
def get_legacy_keyword_rules() -> dict:
    """
    Convert taxonomy to legacy KEYWORD_RULES format for backward compatibility.

    Returns:
        Dictionary in the old KEYWORD_RULES format
    """
    rules = {}

    for cat_key, cat_data in CATEGORY_TAXONOMY.items():
        rules[cat_key] = {
            "name": cat_data["name"],
            "keywords": {}
        }

        # Collect all keywords for this category with weights
        all_keywords = {}
        weight = 1.0

        for sub_data in cat_data["subcategories"].values():
            for sub_sub_data in sub_data["sub_subcategories"].values():
                for keyword in sub_sub_data["keywords"]:
                    if keyword not in all_keywords:
                        # More specific keywords get higher weights
                        all_keywords[keyword] = weight

        rules[cat_key]["keywords"] = all_keywords

    return rules
