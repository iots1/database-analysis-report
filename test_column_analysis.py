#!/usr/bin/env python3
"""
Test script for AI-powered column analysis with sample data.
This demonstrates how to use the enhanced SmartMapper.analyze_column_with_sample() method.
"""

from services.ml_mapper import ml_mapper

def test_column_analysis():
    """Test various column analysis scenarios."""

    print("=" * 80)
    print("HIS Database Column Analysis - Test Suite")
    print("=" * 80)

    # Test Case 1: Thai Buddhist Date
    print("\n[TEST 1] Thai Buddhist Date Column")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="birth_date",
        target_col_name="dob",
        sample_values=[
            "2566-05-15", "2567-03-20", "2565-12-01",
            "2566-08-10", "2567-01-25", "2566-11-05"
        ]
    )
    print_result(result)

    # Test Case 2: Hospital Number (HN)
    print("\n[TEST 2] Hospital Number (HN)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="hn",
        target_col_name="hospital_number",
        sample_values=[
            "1234567", "9876543", "5555555",
            "1111111", "2222222", "3333333"
        ]
    )
    print_result(result)

    # Test Case 3: National ID (CID) with validation
    print("\n[TEST 3] National ID (CID)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="cid",
        target_col_name="citizen_id",
        sample_values=[
            "1234567890123", "9876543210987", "1111111111111",
            "2222222222222", "3333333333333", "4444444444444"
        ]
    )
    print_result(result)

    # Test Case 4: Float IDs that should be integers
    print("\n[TEST 4] Float IDs (should convert to INT)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="patient_id",
        target_col_name="patient_code",
        sample_values=[
            "123.0", "456.0", "789.0",
            "1011.0", "1213.0", "1415.0"
        ]
    )
    print_result(result)

    # Test Case 5: String with whitespace issues
    print("\n[TEST 5] Strings with Whitespace Issues")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="patient_name",
        target_col_name="full_name",
        sample_values=[
            "  John Doe  ", "Jane  Smith", "  Bob   Wilson  ",
            "Alice Brown", "  Charlie  Davis  ", "Eve Johnson"
        ]
    )
    print_result(result)

    # Test Case 6: All NULL/Empty values (should ignore)
    print("\n[TEST 6] All NULL/Empty Values (Should Ignore)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="unused_field",
        target_col_name="unused_column",
        sample_values=[
            None, "", "  ", None, "NaN", None, ""
        ]
    )
    print_result(result)

    # Test Case 7: All zeros (non-count field - should ignore)
    print("\n[TEST 7] All Zeros (Should Ignore)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="legacy_id",
        target_col_name="old_reference",
        sample_values=[
            "0", "0", "0.0", "00", "0", "0"
        ]
    )
    print_result(result)

    # Test Case 8: JSON data
    print("\n[TEST 8] JSON Data")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="metadata",
        target_col_name="extra_data",
        sample_values=[
            '{"key": "value"}', '{"name": "John"}', '{"age": 30}',
            '{"city": "Bangkok"}', '{"status": "active"}', '{"type": "patient"}'
        ]
    )
    print_result(result)

    # Test Case 9: ISO Date (already in good format)
    print("\n[TEST 9] ISO Date Format (Already Good)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="created_at",
        target_col_name="created_date",
        sample_values=[
            "2024-01-15", "2024-02-20", "2024-03-10",
            "2024-04-05", "2024-05-25", "2024-06-30"
        ]
    )
    print_result(result)

    # Test Case 10: ID with leading zeros (should preserve as string)
    print("\n[TEST 10] ID with Leading Zeros")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="department_code",
        target_col_name="dept_id",
        sample_values=[
            "001", "002", "003", "010", "025", "099"
        ]
    )
    print_result(result)

    # Test Case 11: Mismatched HN mapping (low confidence)
    print("\n[TEST 11] Mismatched Mapping (HN -> Email)")
    print("-" * 80)
    result = ml_mapper.analyze_column_with_sample(
        source_col_name="hn",
        target_col_name="email",  # Wrong target!
        sample_values=[
            "1234567", "9876543", "5555555",
            "1111111", "2222222", "3333333"
        ]
    )
    print_result(result)

    print("\n" + "=" * 80)
    print("Test Suite Completed!")
    print("=" * 80)


def print_result(result):
    """Pretty print analysis results."""
    print(f"Confidence Score: {result['confidence_score']:.2f}")
    print(f"Is Match: {result['is_match']}")
    print(f"Should Ignore: {result['should_ignore']}")
    print(f"Transformers: {result['transformers'] if result['transformers'] else 'None'}")
    print(f"Reason: {result['reason']}")


if __name__ == "__main__":
    test_column_analysis()
