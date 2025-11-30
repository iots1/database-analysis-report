import re
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd


class DataTransformer:
    """
    Handles data transformations for migration operations.
    Applies transformations specified in the config mappings.
    """

    @staticmethod
    def transform_value(value: Any, transformers: List[str]) -> Any:
        """
        Apply a sequence of transformers to a value.

        Args:
            value: The value to transform
            transformers: List of transformer names

        Returns:
            Transformed value
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return value

        for transformer in transformers:
            try:
                value = DataTransformer._apply_transformer(value, transformer)
            except Exception as e:
                print(f"Error applying {transformer}: {e}")
                continue

        return value

    @staticmethod
    def _apply_transformer(value: Any, transformer: str) -> Any:
        """Apply a single transformer to a value."""

        # String transformations
        if transformer == "TRIM":
            return str(value).strip() if value else value

        elif transformer == "UPPER_TRIM":
            return str(value).strip().upper() if value else value

        elif transformer == "LOWER_TRIM":
            return str(value).strip().lower() if value else value

        # Date transformations
        elif transformer == "BUDDHIST_TO_ISO":
            return DataTransformer._buddhist_to_iso(value)

        elif transformer == "ENG_DATE_TO_ISO":
            return DataTransformer._eng_date_to_iso(value)

        # Name splitting
        elif transformer == "SPLIT_THAI_NAME":
            # Returns Thai name, splits by space
            return str(value).strip() if value else value

        elif transformer == "SPLIT_ENG_NAME":
            # Returns English name, splits by space
            return str(value).strip() if value else value

        # Phone and gender
        elif transformer == "FORMAT_PHONE":
            return DataTransformer._format_phone(value)

        elif transformer == "MAP_GENDER":
            return DataTransformer._map_gender(value)

        # Number transformations
        elif transformer == "TO_NUMBER":
            try:
                return float(value) if value else None
            except (ValueError, TypeError):
                return None

        elif transformer == "FLOAT_TO_INT":
            try:
                return int(float(value)) if value else None
            except (ValueError, TypeError):
                return None

        elif transformer == "CLEAN_SPACES":
            return re.sub(r'\s+', ' ', str(value).strip()) if value else value

        # String operations
        elif transformer == "REMOVE_PREFIX":
            # This would need specific prefix in mapping configuration
            return str(value).strip() if value else value

        elif transformer == "REPLACE_EMPTY_WITH_NULL":
            return None if (value is None or str(value).strip() == '') else value

        # Lookup operations (would need reference data)
        elif transformer == "LOOKUP_VISIT_ID":
            return value  # Placeholder for lookup operation

        elif transformer == "LOOKUP_PATIENT_ID":
            return value  # Placeholder for lookup operation

        elif transformer == "LOOKUP_DOCTOR_ID":
            return value  # Placeholder for lookup operation

        # JSON parsing
        elif transformer == "PARSE_JSON":
            try:
                if isinstance(value, str):
                    import json
                    return json.loads(value)
                return value
            except:
                return value

        return value

    @staticmethod
    def _buddhist_to_iso(value: Any) -> str:
        """Convert Buddhist year to ISO format date."""
        try:
            value_str = str(value).strip()
            # Assume format like YYYY-MM-DD in Buddhist calendar
            parts = value_str.split('-')
            if len(parts) == 3:
                year = int(parts[0]) - 543  # Buddhist to ISO
                month = int(parts[1])
                day = int(parts[2])
                return f"{year:04d}-{month:02d}-{day:02d}"
            return value_str
        except:
            return value

    @staticmethod
    def _eng_date_to_iso(value: Any) -> str:
        """Convert English date format to ISO format."""
        try:
            value_str = str(value).strip()
            # Try common English formats
            for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(value_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            return value_str
        except:
            return value

    @staticmethod
    def _format_phone(value: Any) -> str:
        """Format phone number to standard format."""
        try:
            # Remove non-digits
            digits = re.sub(r'\D', '', str(value))

            # Format based on length
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11:
                return f"+{digits[0]} {digits[1:4]}-{digits[4:7]}-{digits[7:]}"
            return digits
        except:
            return value

    @staticmethod
    def _map_gender(value: Any) -> str:
        """Map gender values to standard format."""
        try:
            value_str = str(value).strip().upper()

            gender_map = {
                'M': 'M', 'MALE': 'M', '1': 'M',
                'F': 'F', 'FEMALE': 'F', '2': 'F',
                'O': 'O', 'OTHER': 'O', '3': 'O'
            }

            return gender_map.get(value_str, value_str)
        except:
            return value

    @staticmethod
    def apply_mapping_transformers(row: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply transformers specified in a mapping to a row of data.

        Args:
            row: Dictionary of column values
            mapping: Mapping configuration with transformers

        Returns:
            Dictionary with transformed values
        """
        transformed_row = {}

        for key, value in row.items():
            # Find matching mapping for this source column
            matching_mapping = mapping.get(key)

            if matching_mapping and 'transformers' in matching_mapping:
                transformers = matching_mapping['transformers']
                transformed_row[matching_mapping['target']] = DataTransformer.transform_value(
                    value,
                    transformers
                )
            else:
                transformed_row[key] = value

        return transformed_row

    @staticmethod
    def apply_transformers_to_batch(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply transformers to a batch of data (DataFrame).

        Args:
            df: Pandas DataFrame with source data
            config: Migration configuration with mappings

        Returns:
            Transformed DataFrame
        """
        try:
            if df.empty or 'mappings' not in config:
                return df

            # Build transformer map from config
            transformer_map = {}
            for mapping in config.get('mappings', []):
                source_col = mapping.get('source')
                target_col = mapping.get('target')
                transformers = mapping.get('transformers', [])

                if source_col and transformers:
                    transformer_map[source_col] = {
                        'target': target_col,
                        'transformers': transformers
                    }

            # Apply transformers to each column
            for source_col, trans_config in transformer_map.items():
                if source_col in df.columns:
                    df[source_col] = df[source_col].apply(
                        lambda x: DataTransformer.transform_value(x, trans_config['transformers'])
                    )

            return df
        except Exception as e:
            print(f"Error applying batch transformers: {e}")
            return df
