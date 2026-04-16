//! ASCII detection tests - Rust native implementation.

use chardet_rs::pipeline::ascii::detect_ascii;

#[test]
fn test_pure_ascii() {
    let result = detect_ascii(b"Hello world");
    assert!(result.is_some());
    let result = result.unwrap();
    assert_eq!(result.encoding, Some("ascii".to_string()));
    assert_eq!(result.confidence, 1.0);
}

#[test]
fn test_ascii_with_tabs_and_newlines() {
    let result = detect_ascii(b"Hello\tworld\nLine 2\r\nLine 3");
    assert!(result.is_some());
    assert_eq!(result.unwrap().encoding, Some("ascii".to_string()));
}

#[test]
fn test_not_ascii_with_high_bytes() {
    let result = detect_ascii(b"Hello \xc3\xa9nd"); // UTF-8 é
    assert_eq!(result, None);
}

#[test]
fn test_empty_is_none() {
    // Empty input returns None for ASCII detection (no data to analyze)
    let result = detect_ascii(b"");
    assert_eq!(result, None);
}

#[test]
fn test_ascii_with_control_chars() {
    // Allow tabs, newlines, carriage returns
    let result = detect_ascii(b"Hello\x09world\x0A\x0D");
    assert!(result.is_some());
}

#[test]
fn test_not_ascii_with_del() {
    // DEL (0x7F) is not printable ASCII
    let result = detect_ascii(b"Hello\x7Fworld");
    assert_eq!(result, None);
}

#[test]
fn test_all_printable_ascii() {
    // All printable ASCII chars 0x20-0x7E
    let all_printable: Vec<u8> = (0x20..=0x7E).collect();
    let result = detect_ascii(&all_printable);
    assert!(result.is_some());
}
