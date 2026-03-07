//! UTF-8 validation tests - Rust native implementation.
//!
//! These tests mirror the Python tests in tests/test_utf8.py.

use _chardet_rs::pipeline::utf8::detect_utf8;

#[test]
fn test_valid_utf8_with_multibyte() {
    let data = "Héllo wörld café".as_bytes();
    let result = detect_utf8(data);
    assert!(result.is_some());
    assert_eq!(result.as_ref().unwrap().encoding, Some("utf-8".to_string()));
    assert!(result.unwrap().confidence >= 0.9);
}

#[test]
fn test_valid_utf8_chinese() {
    let data = "你好世界".as_bytes();
    let result = detect_utf8(data);
    assert!(result.is_some());
    assert_eq!(result.unwrap().encoding, Some("utf-8".to_string()));
}

#[test]
fn test_valid_utf8_emoji() {
    let data = "Hello 🌍🌎🌏".as_bytes();
    let result = detect_utf8(data);
    assert!(result.is_some());
    assert_eq!(result.unwrap().encoding, Some("utf-8".to_string()));
}

#[test]
fn test_pure_ascii_returns_none() {
    let result = detect_utf8(b"Hello world");
    assert_eq!(result, None);
}

#[test]
fn test_invalid_utf8() {
    let result = detect_utf8(b"\xc3\x00");
    assert_eq!(result, None);
}

#[test]
fn test_overlong_encoding() {
    // Overlong 2-byte sequence
    let result = detect_utf8(b"\xc0\xaf");
    assert_eq!(result, None);
}

#[test]
fn test_invalid_start_byte() {
    let result = detect_utf8(b"\xff\xfe");
    assert_eq!(result, None);
}

#[test]
fn test_truncated_multibyte() {
    let result = detect_utf8(b"Hello \xc3");
    assert_eq!(result, None);
}

#[test]
fn test_empty_input() {
    let result = detect_utf8(b"");
    assert_eq!(result, None);
}

#[test]
fn test_latin1_is_not_valid_utf8() {
    // Latin-1 encoded text
    let text = "Héllo";
    let latin1_bytes: Vec<u8> = text.chars().map(|c| c as u8).collect();
    let result = detect_utf8(&latin1_bytes);
    assert_eq!(result, None);
}

#[test]
fn test_surrogate_pair_rejected() {
    // U+D800 would encode as ED A0 80 in invalid UTF-8
    let result = detect_utf8(b"Hello \xed\xa0\x80 World");
    assert_eq!(result, None);
}

#[test]
fn test_overlong_3byte_rejected() {
    // Overlong 3-byte sequence (E0 80 80) encoding U+0000 must be rejected.
    let result = detect_utf8(b"Hello \xe0\x80\x80 World");
    assert_eq!(result, None);
}

#[test]
fn test_overlong_4byte_rejected() {
    // Overlong 4-byte sequence (F0 80 80 80) encoding U+0000 must be rejected.
    let result = detect_utf8(b"Hello \xf0\x80\x80\x80 World");
    assert_eq!(result, None);
}

#[test]
fn test_above_unicode_max_rejected() {
    // Code point above U+10FFFF (F4 90 80 80 = U+110000) must be rejected.
    let result = detect_utf8(b"Hello \xf4\x90\x80\x80 World");
    assert_eq!(result, None);
}
