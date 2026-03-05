//! Early detection of escape-sequence-based encodings (ISO-2022, HZ-GB-2312, UTF-7).

use super::{DetectionResult, DETERMINISTIC_CONFIDENCE};

/// Detect ISO-2022, HZ-GB-2312, and UTF-7 from escape/tilde/plus sequences.
pub fn detect_escape_encoding(data: &[u8]) -> Option<DetectionResult> {
    let has_esc = data.contains(&0x1B);
    let has_tilde = data.contains(&b'~');
    let has_plus = data.contains(&b'+');
    
    if !has_esc && !has_tilde && !has_plus {
        return None;
    }
    
    // ISO-2022-JP family: check for base ESC sequences, then classify variant.
    if has_esc {
        // Check for JIS X 0208 sequences
        if contains_subsequence(data, b"\x1b$B") || 
           contains_subsequence(data, b"\x1b$@") ||
           contains_subsequence(data, b"\x1b(J") {
            // JIS X 0213 designation -> modern Japanese branch
            if contains_subsequence(data, b"\x1b$(O") || 
               contains_subsequence(data, b"\x1b$(P") {
                return Some(DetectionResult::new(
                    Some("iso2022-jp-2004"),
                    DETERMINISTIC_CONFIDENCE,
                    Some("ja"),
                ));
            }
            // Half-width katakana SI/SO markers (0x0E / 0x0F)
            if data.contains(&0x0E) && data.contains(&0x0F) {
                return Some(DetectionResult::new(
                    Some("iso2022-jp-ext"),
                    DETERMINISTIC_CONFIDENCE,
                    Some("ja"),
                ));
            }
            // Multinational designations or base codes -> broadest multinational
            return Some(DetectionResult::new(
                Some("iso2022-jp-2"),
                DETERMINISTIC_CONFIDENCE,
                Some("ja"),
            ));
        }
        
        // ISO-2022-KR: ESC sequence for KS C 5601
        if contains_subsequence(data, b"\x1b$)C") {
            return Some(DetectionResult::new(
                Some("iso-2022-kr"),
                DETERMINISTIC_CONFIDENCE,
                Some("ko"),
            ));
        }
    }
    
    // HZ-GB-2312: tilde escapes for GB2312
    // Require valid GB2312 byte pairs (0x21-0x7E range) between ~{ and ~} markers.
    if has_tilde && 
       contains_subsequence(data, b"~{") && 
       contains_subsequence(data, b"~}") &&
       has_valid_hz_regions(data) {
        return Some(DetectionResult::new(
            Some("hz-gb-2312"),
            DETERMINISTIC_CONFIDENCE,
            Some("zh"),
        ));
    }
    
    // UTF-7: plus-sign shifts into Base64-encoded Unicode.
    // UTF-7 is a 7-bit encoding: every byte must be in 0x00-0x7F.
    if has_plus && data.iter().all(|&b| b < 0x80) && has_valid_utf7_sequences(data) {
        return Some(DetectionResult::new(
            Some("utf-7"),
            DETERMINISTIC_CONFIDENCE,
            None,
        ));
    }
    
    None
}

fn contains_subsequence(data: &[u8], pattern: &[u8]) -> bool {
    if pattern.is_empty() || data.len() < pattern.len() {
        return false;
    }
    data.windows(pattern.len()).any(|window| window == pattern)
}

fn has_valid_hz_regions(data: &[u8]) -> bool {
    // Check that at least one ~{...~} region contains valid GB2312 byte pairs.
    let mut start = 0;
    loop {
        let begin = find_subsequence(&data[start..], b"~{");
        if begin.is_none() {
            return false;
        }
        let begin = start + begin.unwrap();
        let end = find_subsequence(&data[begin + 2..], b"~}");
        if end.is_none() {
            return false;
        }
        let end = begin + 2 + end.unwrap();
        let region = &data[begin + 2..end];
        
        // Must be non-empty, even length, and all bytes in GB2312 range
        if region.len() >= 2 &&
           region.len() % 2 == 0 &&
           region.iter().all(|&b| (0x21..=0x7E).contains(&b)) {
            return true;
        }
        start = end + 2;
    }
}

fn find_subsequence(data: &[u8], pattern: &[u8]) -> Option<usize> {
    if pattern.is_empty() || data.len() < pattern.len() {
        return None;
    }
    data.windows(pattern.len()).position(|window| window == pattern)
}

// Base64 alphabet used inside UTF-7 shifted sequences (+<Base64>-)
const B64_CHARS: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

fn has_valid_utf7_sequences(data: &[u8]) -> bool {
    let mut start = 0;
    loop {
        let shift_pos = data[start..].iter().position(|&b| b == b'+');
        if shift_pos.is_none() {
            return false;
        }
        let shift_pos = start + shift_pos.unwrap();
        let pos = shift_pos + 1; // skip the '+'
        
        if pos >= data.len() {
            return false;
        }
        
        // +- is a literal plus, not a shifted sequence
        if data[pos] == b'-' {
            start = pos + 1;
            continue;
        }
        
        // Guard: if the '+' is embedded in a base64 stream, it's not real UTF-7
        if is_embedded_in_base64(data, shift_pos) {
            start = pos;
            continue;
        }
        
        // Collect consecutive Base64 characters
        let mut i = pos;
        while i < data.len() && B64_CHARS.contains(&data[i]) {
            i += 1;
        }
        let b64_len = i - pos;
        
        // Accept if base64 content is valid UTF-16BE (at least 3 chars for one code unit)
        if b64_len >= 3 && is_valid_utf7_b64(&data[pos..i]) {
            return true;
        }
        start = i;
    }
}

fn is_embedded_in_base64(data: &[u8], pos: usize) -> bool {
    // Return True if the '+' at pos is embedded in a base64 stream
    let mut count = 0;
    let mut i = pos.saturating_sub(1);
    
    while i > 0 {
        let b = data[i];
        if b == 0x0A || b == 0x0D {
            // Skip newlines
            if i == 0 { break; }
            i -= 1;
            continue;
        }
        if B64_CHARS.contains(&b) || b == b'=' {
            count += 1;
            if i == 0 { break; }
            i -= 1;
        } else {
            break;
        }
    }
    
    count >= 4
}

fn is_valid_utf7_b64(b64_bytes: &[u8]) -> bool {
    // Check if base64 bytes decode to valid UTF-16BE with correct padding.
    let n = b64_bytes.len();
    let total_bits = n * 6;
    
    // Check that padding bits are zero
    let padding_bits = total_bits % 16;
    if padding_bits > 0 {
        let last_val = base64_decode(b64_bytes[n - 1]);
        if last_val.is_none() {
            return false;
        }
        let mask = (1 << padding_bits) - 1;
        if last_val.unwrap() & mask != 0 {
            return false;
        }
    }
    
    // Decode to raw bytes and validate as UTF-16BE
    let num_bytes = total_bits / 8;
    let mut raw = Vec::with_capacity(num_bytes);
    let mut bit_buf = 0u32;
    let mut bit_count = 0;
    
    for &c in b64_bytes {
        let val = base64_decode(c).unwrap_or(0);
        bit_buf = (bit_buf << 6) | val as u32;
        bit_count += 6;
        if bit_count >= 8 {
            bit_count -= 8;
            raw.push(((bit_buf >> bit_count) & 0xFF) as u8);
        }
    }
    
    // Validate UTF-16BE: check for lone surrogates
    let mut prev_high = false;
    for chunk in raw.chunks_exact(2) {
        let code_unit = ((chunk[0] as u16) << 8) | (chunk[1] as u16);
        
        if (0xD800..=0xDBFF).contains(&code_unit) {
            // High surrogate
            if prev_high {
                return false; // Consecutive high surrogates
            }
            prev_high = true;
        } else if (0xDC00..=0xDFFF).contains(&code_unit) {
            // Low surrogate
            if !prev_high {
                return false; // Lone low surrogate
            }
            prev_high = false;
        } else {
            if prev_high {
                return false; // High surrogate not followed by low
            }
        }
    }
    
    !prev_high
}

fn base64_decode(c: u8) -> Option<u8> {
    match c {
        b'A'..=b'Z' => Some(c - b'A'),
        b'a'..=b'z' => Some(c - b'a' + 26),
        b'0'..=b'9' => Some(c - b'0' + 52),
        b'+' => Some(62),
        b'/' => Some(63),
        _ => None,
    }
}
