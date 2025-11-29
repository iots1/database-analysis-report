#!/usr/bin/env python3
"""
Simple test for AI column analysis helper functions (no ML model required).
Tests the pattern detection logic without loading the sentence transformer model.
"""

import re


def test_pattern_detection():
    """Test individual pattern detection functions."""

    print("=" * 80)
    print("AI Column Analysis - Simple Pattern Detection Tests")
    print("=" * 80)

    # Test 1: Thai Buddhist Year Detection
    print("\n[TEST 1] Thai Buddhist Year Detection")
    print("-" * 80)
    samples = ["2566-05-15", "2567-03-20", "2565-12-01"]
    thai_year_pattern = r'25[5-9]\d'
    matches = sum(1 for s in samples if re.search(thai_year_pattern, s))
    print(f"Samples: {samples}")
    print(f"Pattern: {thai_year_pattern}")
    print(f"Matches: {matches}/{len(samples)}")
    print(f"Result: {'✅ PASS - Thai dates detected' if matches == len(samples) else '❌ FAIL'}")

    # Test 2: ISO Date Pattern
    print("\n[TEST 2] ISO Date Format Detection")
    print("-" * 80)
    samples = ["2024-01-15", "2024-02-20", "2024-03-10"]
    iso_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
    matches = sum(1 for s in samples if re.search(iso_pattern, s))
    print(f"Samples: {samples}")
    print(f"Pattern: {iso_pattern}")
    print(f"Matches: {matches}/{len(samples)}")
    print(f"Result: {'✅ PASS - ISO dates detected' if matches == len(samples) else '❌ FAIL'}")

    # Test 3: Float to Int Pattern
    print("\n[TEST 3] Float ID Detection (123.0)")
    print("-" * 80)
    samples = ["123.0", "456.0", "789.0"]
    float_zero_pattern = r'^\d+\.0+$'
    matches = sum(1 for s in samples if re.search(float_zero_pattern, s))
    print(f"Samples: {samples}")
    print(f"Pattern: {float_zero_pattern}")
    print(f"Matches: {matches}/{len(samples)}")
    print(f"Result: {'✅ PASS - Float IDs detected' if matches == len(samples) else '❌ FAIL'}")

    # Test 4: Whitespace Detection
    print("\n[TEST 4] Whitespace Detection")
    print("-" * 80)
    samples = ["  John  ", "Jane", "  Bob  "]
    whitespace_count = sum(1 for s in samples if s != s.strip())
    print(f"Samples: {repr(samples)}")
    print(f"With whitespace: {whitespace_count}/{len(samples)}")
    print(f"Result: {'✅ PASS - Whitespace detected' if whitespace_count > 0 else '❌ FAIL'}")

    # Test 5: HN Pattern
    print("\n[TEST 5] Hospital Number (HN) Pattern")
    print("-" * 80)
    samples = ["1234567", "9876543", "5555555"]
    hn_pattern = r'^\d{6,10}$'
    matches = sum(1 for s in samples if re.match(hn_pattern, s))
    print(f"Samples: {samples}")
    print(f"Pattern: {hn_pattern}")
    print(f"Matches: {matches}/{len(samples)}")
    print(f"Result: {'✅ PASS - HN pattern matched' if matches == len(samples) else '❌ FAIL'}")

    # Test 6: CID Pattern (13 digits)
    print("\n[TEST 6] National ID (CID) Pattern")
    print("-" * 80)
    samples = ["1234567890123", "9876543210987", "1111111111111"]
    cid_pattern = r'^\d{13}$'
    matches = sum(1 for s in samples if re.match(cid_pattern, s))
    print(f"Samples: {samples}")
    print(f"Pattern: {cid_pattern}")
    print(f"Matches: {matches}/{len(samples)}")
    print(f"Result: {'✅ PASS - CID pattern matched' if matches == len(samples) else '❌ FAIL'}")

    # Test 7: JSON Detection
    print("\n[TEST 7] JSON Structure Detection")
    print("-" * 80)
    samples = ['{"key": "value"}', '{"name": "John"}', '{"age": 30}']
    json_indicators = sum(1 for s in samples if s.startswith('{') or s.startswith('['))
    print(f"Samples: {samples[:2]}...")
    print(f"JSON structures: {json_indicators}/{len(samples)}")
    print(f"Result: {'✅ PASS - JSON detected' if json_indicators == len(samples) else '❌ FAIL'}")

    # Test 8: All Zeros Detection
    print("\n[TEST 8] All Zeros Detection")
    print("-" * 80)
    samples = ["0", "0", "0.0", "00"]
    all_zeros = all(str(s).strip() in ['0', '0.0', '00'] for s in samples)
    print(f"Samples: {samples}")
    print(f"All zeros: {all_zeros}")
    print(f"Result: {'✅ PASS - All zeros detected' if all_zeros else '❌ FAIL'}")

    # Test 9: Leading Zeros (IDs)
    print("\n[TEST 9] Leading Zeros Detection")
    print("-" * 80)
    samples = ["001", "002", "010", "025"]
    has_leading_zeros = any(s.startswith('0') and s.isdigit() and len(s) > 1 for s in samples)
    print(f"Samples: {samples}")
    print(f"Has leading zeros: {has_leading_zeros}")
    print(f"Result: {'✅ PASS - Leading zeros detected' if has_leading_zeros else '❌ FAIL'}")

    # Test 10: Empty/NULL Values
    print("\n[TEST 10] Empty/NULL Values Detection")
    print("-" * 80)
    samples = [None, "", "  ", "NaN", "null"]
    valid_values = [v for v in samples if v is not None and str(v).strip() not in ["", "NaN", "None", "null"]]
    is_empty = len(valid_values) == 0
    print(f"Samples: {samples}")
    print(f"Valid values: {len(valid_values)}/{len(samples)}")
    print(f"Result: {'✅ PASS - Empty data detected' if is_empty else '❌ FAIL'}")

    # Test 11: Multiple Spaces
    print("\n[TEST 11] Multiple Consecutive Spaces")
    print("-" * 80)
    samples = ["John  Doe", "Jane   Smith", "Bob    Wilson"]
    multi_space_count = sum(1 for s in samples if re.search(r'\s{2,}', s))
    print(f"Samples: {repr(samples)}")
    print(f"With multiple spaces: {multi_space_count}/{len(samples)}")
    print(f"Result: {'✅ PASS - Multiple spaces detected' if multi_space_count == len(samples) else '❌ FAIL'}")

    # Test 12: Mixed Date Formats
    print("\n[TEST 12] Mixed Date Format Detection")
    print("-" * 80)
    samples = ["15/05/2024", "2024-06-20", "07-15-2024"]
    date_indicators = sum(1 for s in samples if re.search(r'\d{2,4}[-/]\d{1,2}', s))
    print(f"Samples: {samples}")
    print(f"Date patterns: {date_indicators}/{len(samples)}")
    print(f"Result: {'✅ PASS - Mixed dates detected' if date_indicators == len(samples) else '❌ FAIL'}")

    print("\n" + "=" * 80)
    print("Pattern Detection Tests Completed!")
    print("=" * 80)


def test_his_dictionary_matching():
    """Test HIS dictionary keyword matching."""

    print("\n" + "=" * 80)
    print("HIS Dictionary Keyword Matching Tests")
    print("=" * 80)

    his_dictionary = {
        "hn": ["hn", "hospital_number", "mrn", "patient_code"],
        "vn": ["vn", "visit_number", "visit_no"],
        "an": ["an", "admission_number", "admit_no"],
        "cid": ["cid", "national_id", "card_id", "citizen_id", "id_card"],
    }

    test_cases = [
        ("hn", "hospital_number", True),
        ("patient_hn", "mrn", True),
        ("vn", "visit_no", True),
        ("cid", "citizen_id", True),
        ("random_field", "another_field", False),
    ]

    for src, tgt, expected in test_cases:
        src_lower = src.lower()
        tgt_lower = tgt.lower()
        found_match = False

        for key, possible_targets in his_dictionary.items():
            if src_lower == key or src_lower in possible_targets:
                if tgt_lower == key or tgt_lower in possible_targets:
                    found_match = True
                    break

        status = "✅ PASS" if (found_match == expected) else "❌ FAIL"
        print(f"{status} | Source: '{src}' -> Target: '{tgt}' | Expected: {expected}, Got: {found_match}")

    print("=" * 80)


if __name__ == "__main__":
    test_pattern_detection()
    test_his_dictionary_matching()
