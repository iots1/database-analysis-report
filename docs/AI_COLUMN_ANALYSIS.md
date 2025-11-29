# AI-Powered Column Analysis Guide

## Overview

The HIS Database Migration Toolkit now includes advanced AI-powered column analysis that examines **actual sample data** to provide intelligent recommendations for:

- Data transformation rules
- Column mapping validation
- Data quality issues detection
- Healthcare-specific pattern recognition

## Features

### 1. Intelligent Pattern Detection

The system analyzes sample values to detect:

- **Date Formats**: Thai Buddhist dates, ISO dates, mixed formats
- **String Quality**: Whitespace issues, multiple spaces, JSON structures
- **Numeric Patterns**: Float IDs, all-zero placeholders, leading zeros
- **Healthcare Identifiers**: HN, VN, AN, CID with format validation

### 2. Confidence Scoring

Each analysis provides a confidence score (0.0 - 1.0) indicating:

- **0.9-1.0**: High confidence - clear pattern detected
- **0.7-0.8**: Medium-high confidence - likely correct
- **0.5-0.6**: Medium confidence - possible match
- **0.0-0.4**: Low confidence - uncertain or mismatch

### 3. Automatic Transformer Suggestions

Based on sample data, the system recommends appropriate transformers:

| Transformer | When Applied | Example |
|-------------|--------------|---------|
| `BUDDHIST_TO_ISO` | Thai Buddhist year detected (25xx) | "2566-05-15" → "2023-05-15" |
| `ENG_DATE_TO_ISO` | Mixed date formats | "15/05/2023" → "2023-05-15" |
| `TRIM` | Leading/trailing whitespace | "  John  " → "John" |
| `CLEAN_SPACES` | Multiple consecutive spaces | "John  Doe" → "John Doe" |
| `FLOAT_TO_INT` | Float format IDs | "123.0" → "123" |
| `PARSE_JSON` | JSON structures | '{"key":"value"}' |

## API Reference

### `SmartMapper.analyze_column_with_sample()`

Performs comprehensive analysis using sample data.

```python
from services.ml_mapper import ml_mapper

result = ml_mapper.analyze_column_with_sample(
    source_col_name="birth_date",
    target_col_name="dob",
    sample_values=["2566-05-15", "2567-03-20", "2565-12-01"]
)
```

**Returns:**
```python
{
    "confidence_score": 0.85,        # 0.0-1.0
    "is_match": True,                # Source-Target compatibility
    "transformers": ["BUDDHIST_TO_ISO"],  # Recommended transformers
    "should_ignore": False,          # True if column should be ignored
    "reason": "Detected Thai Buddhist year (25xx) in 3/3 samples"
}
```

### Database Integration Functions

#### `get_column_sample_values()`

Fetches distinct sample values from a database column for analysis.

```python
from services.db_connector import get_column_sample_values

success, values = get_column_sample_values(
    db_type="MySQL",
    host="localhost",
    port="3306",
    db_name="hospital_db",
    user="root",
    password="password",
    table_name="patients",
    column_name="birth_date",
    limit=20,
    schema=None
)

if success:
    print(f"Sample values: {values}")
```

**Features:**
- Automatically filters out NULL and empty values
- Returns distinct values only
- Supports MySQL, PostgreSQL, and SQL Server
- Handles schema-qualified table names

## Use Cases

### Use Case 1: Thai Healthcare Database Migration

**Scenario**: Migrating from legacy HIS with Thai Buddhist dates

```python
# Sample data from legacy system
samples = ["2566-01-15", "2567-05-20", "2565-12-01"]

result = ml_mapper.analyze_column_with_sample(
    source_col_name="admit_date",
    target_col_name="admission_date",
    sample_values=samples
)

# Output:
# {
#     "confidence_score": 0.9,
#     "is_match": True,
#     "transformers": ["BUDDHIST_TO_ISO"],
#     "should_ignore": False,
#     "reason": "Detected Thai Buddhist year (25xx) in 3/3 samples"
# }
```

### Use Case 2: Data Quality Detection

**Scenario**: Detecting empty/placeholder columns

```python
# All NULL or empty values
samples = [None, "", "  ", None, ""]

result = ml_mapper.analyze_column_with_sample(
    source_col_name="unused_field",
    target_col_name="unused_column",
    sample_values=samples
)

# Output:
# {
#     "confidence_score": 0.9,
#     "is_match": True,
#     "transformers": [],
#     "should_ignore": True,
#     "reason": "All values are null/empty - suggested to ignore"
# }
```

### Use Case 3: ID Format Normalization

**Scenario**: Converting float IDs to integers

```python
# IDs stored as floats
samples = ["123.0", "456.0", "789.0", "1011.0"]

result = ml_mapper.analyze_column_with_sample(
    source_col_name="patient_id",
    target_col_name="patient_code",
    sample_values=samples
)

# Output:
# {
#     "confidence_score": 0.5,
#     "is_match": True,
#     "transformers": ["FLOAT_TO_INT"],
#     "should_ignore": False,
#     "reason": "Detected float format IDs (4/4 samples) - converting to integer"
# }
```

### Use Case 4: Healthcare Identifier Validation

**Scenario**: Validating Hospital Numbers (HN)

```python
samples = ["1234567", "9876543", "5555555"]

result = ml_mapper.analyze_column_with_sample(
    source_col_name="hn",
    target_col_name="hospital_number",
    sample_values=samples
)

# Output:
# {
#     "confidence_score": 1.0,
#     "is_match": True,
#     "transformers": [],
#     "should_ignore": False,
#     "reason": "HN pattern matched (3/3 valid)"
# }
```

## Integration with Schema Mapper

The analysis function is designed to integrate seamlessly with the Schema Mapper UI:

### Option 1: Manual Analysis Button

Add a "🔬 Analyze Column" button that:

1. Fetches sample data from source database
2. Runs analysis
3. Auto-populates transformers
4. Shows confidence indicator

### Option 2: Automatic Batch Analysis

When AI Auto-Map is clicked:

1. For each mapped column pair
2. Fetch sample values
3. Run analysis
4. Apply suggested transformers
5. Mark low-confidence mappings for review

## Pattern Detection Details

### Date Pattern Detection

| Pattern | Regex | Confidence Threshold |
|---------|-------|---------------------|
| Thai Buddhist Year | `25[5-9]\d` | 50% of samples |
| ISO Date | `\d{4}[-/]\d{1,2}[-/]\d{1,2}` | 70% of samples |
| Mixed Dates | `\d{2,4}[-/]\d{1,2}` | 50% of samples |

### Healthcare Patterns

| Pattern | Format | Validation |
|---------|--------|------------|
| Hospital Number (HN) | 6-10 digits | `^\d{6,10}$` |
| National ID (CID) | 13 digits | `^\d{13}$` |
| Visit Number (VN) | Variable | Keyword match |
| Admission Number (AN) | Variable | Keyword match |

### String Quality Checks

- **Whitespace**: Detects any leading/trailing spaces
- **Multiple Spaces**: Triggers on 30%+ samples with `\s{2,}`
- **JSON**: Detects structures starting with `{` or `[`

### Numeric Pattern Detection

- **Float IDs**: 70%+ samples match `^\d+\.0+$`
- **All Zeros**: All samples are "0", "0.0", "00"
- **Leading Zeros**: IDs like "001", "025" (preserved as strings)

## Testing

Run the comprehensive test suite:

```bash
python test_column_analysis.py
```

This tests:
- ✅ Thai Buddhist dates
- ✅ Healthcare identifiers (HN, CID)
- ✅ Float to integer conversion
- ✅ Whitespace detection
- ✅ Empty value detection
- ✅ Zero placeholder detection
- ✅ JSON data detection
- ✅ ISO date validation
- ✅ Leading zero preservation
- ✅ Mismatched mappings

## Error Handling

The analysis is designed to fail gracefully:

```python
# If sample_values is empty or invalid
result = ml_mapper.analyze_column_with_sample(
    source_col_name="column",
    target_col_name="target",
    sample_values=[]
)

# Returns safe defaults:
# {
#     "confidence_score": 0.9,
#     "is_match": True,
#     "transformers": [],
#     "should_ignore": True,
#     "reason": "All values are null/empty - suggested to ignore"
# }
```

## Best Practices

### 1. Sample Size
- **Minimum**: 5-10 values for basic patterns
- **Recommended**: 20 values for reliable analysis
- **Maximum**: 50 values (diminishing returns)

### 2. Data Quality
- Use DISTINCT values to avoid bias
- Filter NULL and empty strings at database level
- Sample from representative date ranges

### 3. Manual Review
- Always review low confidence mappings (< 0.6)
- Verify transformer suggestions with domain experts
- Check edge cases not covered in samples

### 4. Performance
- Database sampling is efficient (uses indexes)
- Analysis runs client-side (no external API calls)
- Connection pooling reuses database connections

## Future Enhancements

Planned features:

- [ ] Validator auto-suggestion (e.g., VALID_DATE for date fields)
- [ ] Custom pattern dictionary per hospital
- [ ] Bulk analysis with progress indicators
- [ ] Analysis result caching
- [ ] Statistical outlier detection
- [ ] Cross-column relationship detection

## Support

For issues or questions:

1. Check test suite: `python test_column_analysis.py`
2. Review sample data quality
3. Verify database connectivity
4. Check [GitHub Issues](https://github.com/yourusername/his-analyzer/issues)

---

**Last Updated**: 2024-01-15
**Version**: 8.1
**Author**: HIS Migration Toolkit Team
