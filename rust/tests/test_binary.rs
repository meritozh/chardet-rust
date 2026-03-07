//! Binary detection tests - Rust native implementation.

use _chardet_rs::pipeline::binary::is_binary;

#[test]
fn test_png_signature() {
    let data = b"\x89PNG\r\n\x1a\n";
    assert!(is_binary(data, 200_000));
}

#[test]
fn test_gif_signature() {
    let data = b"GIF8";
    assert!(is_binary(data, 200_000));
}

#[test]
fn test_jpeg_signature() {
    // JPEG signature needs 4 bytes: \xFF\xD8\xFF followed by any byte
    let data = b"\xFF\xD8\xFF\xE0";
    assert!(is_binary(data, 200_000));
}

#[test]
fn test_zip_signature() {
    let data = b"PK\x03\x04";
    assert!(is_binary(data, 200_000));
}

#[test]
fn test_pdf_signature() {
    let data = b"%PDF-1.4";
    assert!(is_binary(data, 200_000));
}

#[test]
fn test_text_is_not_binary() {
    let data = b"Hello world, this is plain text content.";
    assert!(!is_binary(data, 200_000));
}

#[test]
fn test_empty_is_not_binary() {
    assert!(!is_binary(b"", 200_000));
}

#[test]
fn test_null_bytes_binary() {
    // High percentage of null bytes indicates binary
    let data = vec![0u8; 100];
    assert!(is_binary(&data, 200_000));
}

#[test]
fn test_control_chars_binary() {
    // High percentage of control chars (except whitespace) indicates binary
    let mut data = vec![0x01u8; 50];
    data.extend_from_slice(b"some text");
    assert!(is_binary(&data, 200_000));
}
