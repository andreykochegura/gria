import pandas as pd
from fractions import Fraction
from gria.tools import error, warning, info, Dataset, roundup


INSUFFICIENT_DATA = "Недостаточно данных"


def insufficient(results: list, sample_id: str, feature_name: str):
    results.append({
        "sample_id": sample_id,
        "feature_name": feature_name,
        "score": INSUFFICIENT_DATA,
    })


def is_valid_ploidy(genotype: str, sex: str, chromosome: str) -> bool:
    alleles_count = len(genotype.split("/"))
    sex = sex.lower()
    chromosome = chromosome.upper()
    if chromosome in {"X", "Y"}:
        expected = 1 if sex == "male" else (2 if chromosome == "X" else 0)
        return alleles_count == expected
    else:
        return alleles_count == 2


def normalize_genotype(genotype: str) -> str:
    return "/".join(sorted(genotype.strip().upper().split("/")))


def is_matches_genotype(genotype: str, variant_alleles: str) -> bool:
    genotype = genotype.strip().upper()
    return set(genotype.replace("/", "")).issubset(set(variant_alleles.replace("/", "")))


def is_complemented_genotype(genotype: str, variant_alleles: str) -> bool:
    return is_matches_genotype(get_complement_alleles(genotype), variant_alleles)


def get_complement_alleles(genotype: str) -> str:
    return genotype.translate(str.maketrans("ATGC", "TACG"))


def is_palindromic(alleles: str) -> bool:
    return set(alleles.split("/")) in ({"A", "T"}, {"C", "G"})


def get_threshold(score: Fraction, feature_thresholds: pd.DataFrame) -> dict | None:
    applicable = [row for row in feature_thresholds.to_dict("records") if roundup(score) >= row["lower_bound"]]
    if not applicable:
        return None
    return max(applicable, key=lambda row: row["lower_bound"])


def delete_palindromic_variants(variants: pd.DataFrame) -> pd.DataFrame:
    mask = variants["alleles"].apply(is_palindromic)
    for rsid, pvar in variants[mask].iterrows():
        error(f"Palindromic allele is excluded from analysis. gen: {pvar['gen']}, rsID: {rsid}")
    return variants[~mask].copy()


def analyze(data: Dataset):
    variants = data["variants"].set_index("rsid")
    features = data["features"]
    contributions = data["contributions"]
    thresholds = data["thresholds"]
    samples = data["samples"]
    contribution_index = {(row.feature_code, row.gen, row.rsid, normalize_genotype(row.genotype)): row.contribution for row in contributions.itertuples(index=False)}
    
    variants = delete_palindromic_variants(variants)

    results = []

    for sample in samples.to_dict("records"):
        sample_id = sample["sample_id"]
        for feature in features.to_dict("records"):
            feature_code = feature["feature_code"]
            feature_name = feature["name"]
            feature_variants = [rsid.strip() for rsid in feature["variants"].split(",")]
            score = Fraction(0)
            inputs_used = 0
            failed = False
            for rsid in feature_variants:
                if rsid not in variants.index:
                    error(f"Variant not found. rsID: {rsid}, sample: {sample_id}, feature: {feature_code}")
                    failed = True
                    insufficient(results, sample_id, feature_name)
                    break

                variant = variants.loc[rsid]
                genotype_column = f"{variant.gen} {rsid}"
                genotype = sample.get(genotype_column)

                if pd.isna(genotype) or not str(genotype).strip():
                    continue

                genotype = str(genotype).strip().upper()

                if is_complemented_genotype(genotype, variant.alleles) and not is_matches_genotype(genotype, variant.alleles):
                    warning(f"Strand orientation mismatch: '{genotype}' in '{genotype_column}' of sample '{sample_id}'. Complementing genotype to `{get_complement_alleles(genotype)}`")
                    genotype = get_complement_alleles(genotype)
                elif not is_matches_genotype(genotype, variant.alleles):
                    error(f"Wrong genotype '{genotype}' in '{genotype_column}' of sample '{sample_id}'")
                    failed = True
                    insufficient(results, sample_id, feature_name)
                    break
                
                if not is_valid_ploidy(genotype, sample["sex"], variant["chromosome"]):
                    error(f"Wrong ploidy for genotype '{genotype}' in '{genotype_column}' of sample '{sample_id}'")
                    failed = True
                    insufficient(results, sample_id, feature_name)
                    break

                key = (feature_code, variant.gen, rsid, normalize_genotype(genotype))

                if key not in contribution_index:
                    error(f"Contribution not found for {genotype_column} of sample {sample_id}, genotype: {genotype}")
                    failed = True
                    insufficient(results, sample_id, feature_name)
                    break

                score += contribution_index[key]
                inputs_used += 1

            if failed:
                continue

            if inputs_used < feature["min_inputs"]:
                insufficient(results, sample_id, feature_name)
                continue

            score = score / inputs_used
            feature_thresholds = thresholds[thresholds["feature_code"] == feature_code]
            threshold = get_threshold(score, feature_thresholds)

            if threshold is None:
                error(f"Threshold not found for sample {sample_id} feature {feature_code}: score: {score}.")
                insufficient(results, sample_id, feature_name)
                continue

            results.append({
                "sample_id": sample_id,
                "feature_code": feature_code,
                "feature_name": feature_name,
                "score": roundup(score),
                "inputs_used": inputs_used,
                "level": threshold["level"],
                "conclusion": threshold["conclusion"],
            })

    if not results:
        warning("No results")
        return None
        
    for result in results:
        sample_id = result["sample_id"]
        feature_name = result["feature_name"]
        score = result["score"]

        print(
            f"{sample_id} | {feature_name} | "
            f"{INSUFFICIENT_DATA if score == INSUFFICIENT_DATA else f'Балл: {score} | Уровень: {result["level"]} | Заключение: {result["conclusion"]}'}"
        )
