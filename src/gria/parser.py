from fractions import Fraction
from pathlib import Path
import pandas as pd
from gria.schema import SCHEMA
from gria.tools import warning, error, Dataset


class ParseError(Exception):
    pass


def parse(path) -> Dataset:
    path = Path(path)
    data = load_dataset(path)

    validate_schema(data)
    convert_types(data)
    validate_values(data)
    rename_dataset(data)
    drop_invalid_rows(data)
    remove_duplicates(data)

    return data


def load_dataset(path: Path) -> Dataset:
    if not path.is_file():
        raise FileNotFoundError(f"File not found: '{path}'")

    extension = SCHEMA["extension"]
    if path.suffix.lower() != extension:
        raise ParseError(f"Wrong file extension: expected '{extension}', got '{path.suffix}'")
    try:
        sheets = pd.read_excel(path, sheet_name=None, dtype=object, engine="openpyxl")
        for sheet in sheets.values():
            sheet.replace(r"^\s*$", None, regex=True, inplace=True)
            sheet.dropna(axis=0, how="all", inplace=True)
            sheet.dropna(axis=1, how="all", inplace=True)
            sheet.reset_index(drop=True, inplace=True)
        return sheets
    except Exception as exc:
        raise ParseError(f"Failed to read '{path}': {exc}") from exc


def validate_schema(data: Dataset) -> None:
    expected_sheets = {sheet_schema["name"]: sheet_schema for sheet_schema in SCHEMA["sheets"].values()}

    for sheet_name in data:
        if sheet_name not in expected_sheets:
            pass
            # warning(f"Unexpected sheet '{sheet_name}' was ignored")

    for sheet_name in expected_sheets:
        if sheet_name not in data:
            raise ParseError(f"Sheet is missing: '{sheet_name}'")

    for sheet_name, sheet in data.items():
        if sheet_name not in expected_sheets:
            continue

        sheet_schema = expected_sheets[sheet_name]
        expected_columns = {column["name"] for column in sheet_schema["columns"].values()}
        dynamic_columns = sheet_schema.get("dynamic_columns", {})

        for column_name in sheet.columns:
            if column_name in expected_columns:
                continue

            matched = any(dynamic_schema["name_reg"].fullmatch(column_name) for dynamic_schema in dynamic_columns.values())
            if not matched:
                pass
                # warning(f"Unexpected column '{column_name}' on sheet '{sheet_name}' was ignored")

    for sheet_name, sheet_schema in expected_sheets.items():
        actual_columns = data[sheet_name].columns
        for column in sheet_schema["columns"].values():
            if column["name"] not in actual_columns:
                raise ParseError(f"Column '{column['name']}' is missing on sheet '{sheet_name}'")

    for sheet_name, sheet_schema in expected_sheets.items():
        dynamic_columns = sheet_schema.get("dynamic_columns", {})
        for dynamic_schema in dynamic_columns.values():
            if not any(dynamic_schema["name_reg"].fullmatch(column_name) for column_name in data[sheet_name].columns):
                examples = dynamic_schema.get("name_examples", ["<no examples>"])
                raise ParseError(f"No columns like '{examples}' on '{sheet_name}'")


def convert_value(value, column_type):
    if pd.isna(value):
        return None
    if column_type is Fraction and isinstance(value, float):
        value = repr(value)  # Fraction(0.1) is inexact, Fraction("0.1") is exactly 1/10
    return column_type(value)


def convert_types(data: Dataset) -> None:
    for sheet_schema in SCHEMA["sheets"].values():
        sheet_name = sheet_schema["name"]
        sheet = data[sheet_name]
        columns = sheet_schema["columns"]
        dynamic_columns = sheet_schema.get("dynamic_columns", {})
        column_schemas = {column_schema["name"]: column_schema for column_schema in columns.values()}
        for column_name in sheet.columns:
            column_schema = column_schemas.get(column_name)
            if column_schema is None:
                for dynamic_schema in dynamic_columns.values():
                    if dynamic_schema["name_reg"].fullmatch(column_name):
                        column_schema = dynamic_schema
                        break

            if column_schema is None:
                continue

            column_type = column_schema["type"]
            for i, value in sheet[column_name].items():
                try:
                    sheet.at[i, column_name] = convert_value(value, column_type)  # oh!
                except Exception as exc:
                    error(f"Failed to convert value '{value}' into '{column_type}'. Sheet: '{sheet_name}', "
                          f"column: '{column_name}', index: '{i}'. Value was replaced by 'None'. Error: {exc}")
                    sheet.at[i, column_name] = None


def normalize_choice(value, allowed: set):
    """Match `value` against `allowed` ignoring case and allele order; return the canonical form."""
    text = str(value).strip()
    lookup = {item.casefold(): item for item in allowed}
    for candidate in (text, "/".join(sorted(text.split("/")))):
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]
    raise ValueError("is not an allowed value")


def check_value(value, column_schema: dict):
    """Return the value (normalized where the schema allows it) or raise ValueError with the reason."""
    regex = column_schema.get("regex")
    if regex is not None and not regex.fullmatch(str(value)):
        raise ValueError(f"does not match '{regex.pattern}'")

    allowed = column_schema.get("values")
    if allowed is not None:
        value = normalize_choice(value, allowed)

    min_value = column_schema.get("min_value")
    if min_value is not None and value < min_value:
        raise ValueError(f"is less than {min_value}")

    max_value = column_schema.get("max_value")
    if max_value is not None and value > max_value:
        raise ValueError(f"is greater than {max_value}")

    precision = column_schema.get("precision")
    if precision is not None and (value * 10 ** precision).denominator != 1:
        raise ValueError(f"has more than {precision} decimal places")

    item_regex = column_schema.get("item_regex")
    if item_regex is not None:
        for item in value.split(column_schema.get("delimiter", ",")):
            if not item_regex.fullmatch(item.strip()):
                raise ValueError(f"item '{item.strip()}' does not match '{item_regex.pattern}'")

    return value


def validate_values(data: Dataset) -> None:
    for sheet_schema in SCHEMA["sheets"].values():
        sheet_name = sheet_schema["name"]
        sheet = data[sheet_name]
        column_schemas = {column_schema["name"]: column_schema for column_schema in sheet_schema["columns"].values() }
        dynamic_columns = sheet_schema.get("dynamic_columns", {})

        for column_name in sheet.columns:
            column_schema = column_schemas.get(column_name)
            if column_schema is None:
                for dynamic_schema in dynamic_columns.values():
                    if dynamic_schema["name_reg"].fullmatch(column_name):
                        column_schema = dynamic_schema
                        break

            if column_schema is None:
                continue

            for i, value in sheet[column_name].items():
                if value is None:
                    continue

                try:
                    sheet.at[i, column_name] = check_value(value, column_schema)
                except ValueError as exc:
                    error(f"Failed to validate value '{value}': {exc}. Sheet: '{sheet_name}', column: '{column_name}', index: '{i}'. Value was replaced by 'None'")
                    sheet.at[i, column_name] = None


def drop_invalid_rows(data: Dataset) -> None:
    for sheet_key, sheet_schema in SCHEMA["sheets"].items():
        df = data[sheet_key]
        invalid = df[list(sheet_schema["columns"])].isna().any(axis=1)
        if not invalid.any():
            continue

        indexes = list(df.index[invalid])
        if sheet_schema.get("invalid_rows") == "fail":
            raise ParseError(f"Invalid values on sheet '{sheet_schema['name']}', index: {indexes}. "
                             f"Skipping a row here would silently change the results")

        for i in indexes:
            error(f"Row was dropped because of invalid values. Sheet: '{sheet_schema['name']}', index: '{i}'")
        data[sheet_key] = df[~invalid].reset_index(drop=True)


def remove_duplicates(data: Dataset) -> None:
    for sheet_key, sheet_schema in SCHEMA["sheets"].items():
        df = data[sheet_key]
        unique_keys = sheet_schema["unique_keys"]
        columns_schema = sheet_schema["columns"]
        duplicate_mask = df.duplicated(subset=unique_keys, keep="first")

        for _, record in df.loc[duplicate_mask].iterrows():
            duplicate_values = {columns_schema[column]["name"]: record[column] for column in unique_keys}
            error(f"Duplicate is found. Sheet: '{sheet_schema['name']}', unique fields: {duplicate_values}")

        if duplicate_mask.any():
            data[sheet_key] = (df.drop_duplicates(subset=unique_keys, keep="first").reset_index(drop=True))


def rename_dataset(data: Dataset) -> None:
    for sheet_key, sheet_config in SCHEMA["sheets"].items():
        sheet_name = sheet_config["name"]
        if sheet_name in data:
            df = data.pop(sheet_name)
            column_mapping = {config["name"]: column_key for column_key, config in sheet_config["columns"].items()}
            df.rename(columns=column_mapping, inplace=True)
            data[sheet_key] = df
