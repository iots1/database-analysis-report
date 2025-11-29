#!/usr/bin/env python3
"""
Quick Start Example: AI-Powered Column Analysis

This script demonstrates the simplest way to use the new AI column analysis feature.
"""

from services.ml_mapper import ml_mapper


def example_1_thai_dates():
    """Example 1: Detecting Thai Buddhist dates and suggesting transformers."""

    print("=" * 70)
    print("Example 1: Thai Buddhist Date Detection")
    print("=" * 70)

    # Sample data from a Thai HIS database
    birth_dates = [
        "2566-05-15",  # Thai Buddhist year 2566 = 2023 AD
        "2567-03-20",  # Thai Buddhist year 2567 = 2024 AD
        "2565-12-01",
        "2566-08-10",
        "2567-01-25"
    ]

    # Run analysis
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="birth_date",
        target_col_name="dob",
        sample_values=birth_dates
    )

    # Display results
    print(f"✅ Analysis Complete!\n")
    print(f"   Confidence Score: {result['confidence_score']:.0%}")
    print(f"   Suggested Transformers: {result['transformers']}")
    print(f"   Reason: {result['reason']}")
    print(f"   Should Ignore: {result['should_ignore']}\n")


def example_2_float_ids():
    """Example 2: Detecting float format IDs that should be integers."""

    print("=" * 70)
    print("Example 2: Float ID Detection")
    print("=" * 70)

    # Patient IDs stored as floats (common database export issue)
    patient_ids = ["123.0", "456.0", "789.0", "1011.0", "1213.0"]

    result = ml_mapper.analyze_column_with_sample(
        source_col_name="patient_id",
        target_col_name="patient_code",
        sample_values=patient_ids
    )

    print(f"✅ Analysis Complete!\n")
    print(f"   Confidence Score: {result['confidence_score']:.0%}")
    print(f"   Suggested Transformers: {result['transformers']}")
    print(f"   Reason: {result['reason']}\n")


def example_3_empty_columns():
    """Example 3: Detecting columns with no useful data."""

    print("=" * 70)
    print("Example 3: Empty Column Detection")
    print("=" * 70)

    # A column with no useful data
    unused_field = [None, "", "  ", None, ""]

    result = ml_mapper.analyze_column_with_sample(
        source_col_name="unused_field",
        target_col_name="unused_column",
        sample_values=unused_field
    )

    print(f"✅ Analysis Complete!\n")
    print(f"   Confidence Score: {result['confidence_score']:.0%}")
    print(f"   Suggested Transformers: {result['transformers']}")
    print(f"   Should Ignore: {result['should_ignore']} ⚠️")
    print(f"   Reason: {result['reason']}\n")


def example_4_whitespace_cleanup():
    """Example 4: Detecting string quality issues."""

    print("=" * 70)
    print("Example 4: Whitespace Detection")
    print("=" * 70)

    # Patient names with whitespace issues
    patient_names = [
        "  John Doe  ",
        "Jane  Smith",
        "  Bob   Wilson  ",
        "Alice Brown",
        "  Charlie  Davis  "
    ]

    result = ml_mapper.analyze_column_with_sample(
        source_col_name="patient_name",
        target_col_name="full_name",
        sample_values=patient_names
    )

    print(f"✅ Analysis Complete!\n")
    print(f"   Confidence Score: {result['confidence_score']:.0%}")
    print(f"   Suggested Transformers: {result['transformers']}")
    print(f"   Reason: {result['reason']}\n")


def example_5_healthcare_identifiers():
    """Example 5: Validating healthcare identifiers (HN, CID)."""

    print("=" * 70)
    print("Example 5: Hospital Number (HN) Validation")
    print("=" * 70)

    # Hospital Numbers (7-digit format)
    hospital_numbers = ["1234567", "9876543", "5555555", "1111111"]

    result = ml_mapper.analyze_column_with_sample(
        source_col_name="hn",
        target_col_name="hospital_number",
        sample_values=hospital_numbers
    )

    print(f"✅ Analysis Complete!\n")
    print(f"   Confidence Score: {result['confidence_score']:.0%}")
    print(f"   Is Valid Match: {result['is_match']}")
    print(f"   Reason: {result['reason']}\n")


def example_6_batch_analysis():
    """Example 6: Analyzing multiple columns at once."""

    print("=" * 70)
    print("Example 6: Batch Column Analysis")
    print("=" * 70)

    # Define columns to analyze
    columns = {
        "birth_date": {
            "target": "dob",
            "samples": ["2566-01-15", "2567-05-20", "2565-12-01"]
        },
        "hn": {
            "target": "hospital_number",
            "samples": ["1234567", "9876543", "5555555"]
        },
        "patient_id": {
            "target": "patient_code",
            "samples": ["123.0", "456.0", "789.0"]
        }
    }

    results = {}

    # Analyze all columns
    for col_name, col_info in columns.items():
        result = ml_mapper.analyze_column_with_sample(
            source_col_name=col_name,
            target_col_name=col_info["target"],
            sample_values=col_info["samples"]
        )
        results[col_name] = result

    # Display summary
    print("\n📊 Batch Analysis Results:\n")
    print(f"{'Column':<20} {'Confidence':<12} {'Transformers':<30}")
    print("-" * 70)

    for col_name, result in results.items():
        transformers = ", ".join(result["transformers"]) if result["transformers"] else "None"
        print(f"{col_name:<20} {result['confidence_score']:>6.0%}      {transformers:<30}")

    print()


def example_7_real_world_workflow():
    """Example 7: Complete real-world workflow."""

    print("=" * 70)
    print("Example 7: Real-World Workflow - Patient Table Migration")
    print("=" * 70)

    # Simulating a real patient table with various data types
    print("\n📋 Analyzing Patient Table Columns...\n")

    columns_to_migrate = [
        {
            "source": "PatientHN",
            "target": "hospital_number",
            "samples": ["1234567", "9876543", "5555555"]
        },
        {
            "source": "BirthDate",
            "target": "date_of_birth",
            "samples": ["2566-01-15", "2567-05-20", "2565-12-01"]
        },
        {
            "source": "PatientName",
            "target": "full_name",
            "samples": ["  John Doe  ", "Jane Smith", "  Bob Wilson  "]
        },
        {
            "source": "NationalID",
            "target": "citizen_id",
            "samples": ["1234567890123", "9876543210987", "1111111111111"]
        },
        {
            "source": "LegacyField",
            "target": "unused",
            "samples": [None, "", None, ""]
        }
    ]

    # Analyze each column
    print(f"{'Column':<20} {'Status':<15} {'Action':<40}")
    print("-" * 70)

    for col in columns_to_migrate:
        result = ml_mapper.analyze_column_with_sample(
            source_col_name=col["source"],
            target_col_name=col["target"],
            sample_values=col["samples"]
        )

        # Determine status emoji
        if result["should_ignore"]:
            status = "⚠️ Ignore"
            action = "Skip this column"
        elif result["confidence_score"] >= 0.8:
            status = "✅ High Conf"
            action = f"Apply: {', '.join(result['transformers']) if result['transformers'] else 'No transform'}"
        elif result["confidence_score"] >= 0.6:
            status = "🟡 Medium Conf"
            action = f"Review: {result['reason'][:35]}..."
        else:
            status = "🔴 Low Conf"
            action = "Manual review required"

        print(f"{col['source']:<20} {status:<15} {action:<40}")

    print("\n✅ Analysis Complete! Ready for migration config generation.\n")


def main():
    """Run all examples."""

    print("\n")
    print("🧠 AI-Powered Column Analysis - Quick Start Examples")
    print("=" * 70)
    print()

    example_1_thai_dates()
    example_2_float_ids()
    example_3_empty_columns()
    example_4_whitespace_cleanup()
    example_5_healthcare_identifiers()
    example_6_batch_analysis()
    example_7_real_world_workflow()

    print("=" * 70)
    print("🎉 All Examples Completed!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("  1. Review the documentation in docs/AI_COLUMN_ANALYSIS.md")
    print("  2. Run the test suite: python3 test_analysis_simple.py")
    print("  3. Integrate with Schema Mapper UI (see docs/INTEGRATION_EXAMPLE.md)")
    print()


if __name__ == "__main__":
    main()
