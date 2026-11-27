import re
from fractions import Fraction


GENOTYPE_VALUES = {"A/A", "A/C", "A/G", "A/T", "C/C", "C/G", "C/T", "G/G", "G/T", "T/T", "A", "C", "G", "T"}
CHROMOSOME_VALUES = {*(str(i) for i in range(1, 23)), "X", "Y"}


GENE_REGEX = re.compile(r"^[A-Z][A-Z0-9_-]*$")
RSID_REGEX = re.compile(r"^rs[0-9]+$")
CHROMOSOME_REGEX = re.compile(r"^(?:[1-9]|1[0-9]|2[0-2]|X|Y)$")
ALLELES_REGEX = re.compile(r"^[ACGT]/[ACGT]$")
SAMPLE_REGEX = re.compile(r"^[A-Z][0-9]+$")
GENOTYPE_COLUMN_REGEX = re.compile(r"^[A-Z][A-Z0-9-]*\s+rs[0-9]+$")


SCHEMA = {
    "extension": ".xlsx",
    "sheets": {
        "variants": {
            "name": "Варианты",
            "unique_keys": ["rsid"],
            "columns": {
                "gen": {
                    "name": "Ген",
                    "type": str,
                    "regex": GENE_REGEX,
                    "value_examples": ["SOD2", "ZNF511-PRAP1", "GTF2H2C_2"],
                },
                "rsid": {
                    "name": "rsID",
                    "type": str,
                    "regex": RSID_REGEX,
                    "value_examples": ["rs4880", "rs1050450"],
                },
                "chromosome": {
                    "name": "Хромосома",
                    "type": str,
                    "regex": CHROMOSOME_REGEX,
                    "values": CHROMOSOME_VALUES,
                    "value_examples": ["6", "11", "X", "Y"],
                },
                "alleles": {
                    "name": "Аллели",
                    "type": str,
                    "regex": ALLELES_REGEX,
                    "value_examples": ["C/T", "A/G", "C/G"],
                },
            },
        },
        "features": {
            "unique_keys": ["feature_code"],
            "name": "Признаки",
            "columns": {
                "feature_code": {
                    "name": "Код признака",
                    "type": str,
                },
                "name": {
                    "name": "Название",
                    "type": str,
                },
                "variants": {
                    "name": "Варианты",
                    "type": str,
                    "delimiter": ",",
                    "item_regex": RSID_REGEX,
                    "value_examples": ["rs4880, rs1050450", "rs662799, rs328, rs5128"],
                },
                "min_inputs": {
                    "name": "Минимум входов",
                    "type": int,
                    "min_value": 1,
                    "value_examples": [2, 3],
                },
            },
        },
        "contributions": {
            "name": "Вклады",
            "unique_keys": ["feature_code", "gen", "rsid", "genotype"],
            "columns": {
                "feature_code": {
                    "name": "Код признака",
                    "type": str,
                },
                "gen": {
                    "name": "Ген",
                    "type": str,
                    "regex": GENE_REGEX,
                    "value_examples": ["SOD2", "ZNF511-PRAP1", "GTF2H2C_2"],
                },
                "rsid": {
                    "name": "rsID",
                    "type": str,
                    "regex": RSID_REGEX,
                    "value_examples": ["rs4880", "rs1050450"],
                },
                "genotype": {
                    "name": "Генотип",
                    "type": str,
                    "values": GENOTYPE_VALUES,
                },
                "contribution": {
                    "name": "Вклад",
                    "type": Fraction,
                    "min_value": Fraction("-1"),
                    "max_value": Fraction("1"),
                    "precision": 2,
                },
            },
        },
        "thresholds": {
            "name": "Пороги",
            "unique_keys": ["feature_code", "lower_bound"],
            "columns": {
                "feature_code": {
                    "name": "Код признака",
                    "type": str,
                },
                "lower_bound": {
                    "name": "Нижняя граница",
                    "type": Fraction,
                    "min_value": Fraction("-1"),
                    "max_value": Fraction("1"),
                    "precision": 2,
                },
                "level": {
                    "name": "Уровень",
                    "type": str,
                    "values": {"high", "medium", "low", "protective"},
                },
                "conclusion": {
                    "name": "Заключение",
                    "type": str,
                },
            },
        },
        "samples": {
            "name": "Образцы",
            "unique_keys": ["sample_id"],
            "columns": {
                "sample_id": {
                    "name": "Образец",
                    "type": str,
                    "regex": SAMPLE_REGEX,
                    "value_examples": ["S01", "S02"],
                },
                "sex": {
                    "name": "Пол",
                    "type": str,
                    "values": {"male", "female"},
                },
            },
            "dynamic_columns": {
                "genotypes": {
                    "name_reg": GENOTYPE_COLUMN_REGEX,
                    "name_examples": ["SOD2 rs4880", "GPX1 rs1050450"],
                    "type": str,
                    "values": GENOTYPE_VALUES,
                },
            },
        },
    },
}
